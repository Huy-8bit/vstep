from typing import Literal

from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import exists, func, or_, select

from app.api.deps import DB, CurrentUser
from app.common.errors import AppError
from app.db.base import utcnow
from app.llm.openai_client import OpenAILLMClient
from app.models import ExamSession
from app.models.library import LibraryQuestion, QuestionCollection
from app.models.reading import ReadingExamSession
from app.models.speaking import SpeakingExamSession
from app.repositories.library import QuestionRepository, document_view
from app.schemas.library import (
    CollectionCreate,
    LibraryDocument,
    LibraryOrganize,
    LibraryPractice,
    LibrarySave,
    ParseRequest,
    Skill,
)
from app.services.library_practice_service import LibraryPracticeService
from app.services.library_service import library_view, practice_stats
from app.services.question_import_service import QuestionImportService

router = APIRouter(prefix="/my-questions", tags=["My Question Library"])


@router.get("")
async def list_questions(
    db: DB,
    user: CurrentUser,
    skill: Skill | None = None,
    part: str | None = None,
    search: str = Query(default="", max_length=200),
    topic: str = "",
    tag: str = "",
    favorite: bool = False,
    practiced: bool | None = None,
    collection_id: str | None = None,
    order: Literal["newest", "oldest"] = "newest",
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=24, ge=1, le=100),
):
    query = select(LibraryQuestion).where(
        LibraryQuestion.user_id == user.id, LibraryQuestion.deleted_at.is_(None)
    )
    for column, value in (
        (LibraryQuestion.skill, skill),
        (LibraryQuestion.part, part),
        (LibraryQuestion.topic, topic),
        (LibraryQuestion.collection_id, collection_id),
    ):
        if value:
            query = query.where(column == value)
    if search:
        pattern = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(
            or_(
                LibraryQuestion.title.ilike(pattern),
                LibraryQuestion.source_name.ilike(pattern),
                LibraryQuestion.notes.ilike(pattern),
            )
        )
    if tag:
        query = query.where(LibraryQuestion.tags.contains([tag]))
    if favorite:
        query = query.where(LibraryQuestion.favorite.is_(True))
    if practiced is not None:
        practiced_query = or_(
            *[
                exists(
                    select(model.id).where(
                        model.user_id == user.id, model.library_question_id == LibraryQuestion.id
                    )
                )
                for model in (ExamSession, SpeakingExamSession, ReadingExamSession)
            ]
        )
        query = query.where(practiced_query if practiced else ~practiced_query)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    rows = list(
        await db.scalars(
            query.order_by(
                LibraryQuestion.created_at.desc() if order == "newest" else LibraryQuestion.created_at.asc(),
                LibraryQuestion.id,
            )
            .offset(offset)
            .limit(limit)
        )
    )
    stats = await practice_stats(db, user.id, [r.id for r in rows])
    return {"total": total, "items": [library_view(r, stats[r.id], include_content=False) for r in rows]}


@router.get("/collections")
async def collections(db: DB, user: CurrentUser):
    rows = await db.scalars(
        select(QuestionCollection)
        .where(QuestionCollection.user_id == user.id)
        .order_by(QuestionCollection.name)
    )
    return [{"id": row.id, "name": row.name} for row in rows]


@router.post("/collections", status_code=201)
async def create_collection(data: CollectionCreate, db: DB, user: CurrentUser):
    if not data.name.strip():
        raise AppError(422, "Tên bộ sưu tập không được trống.")
    row = QuestionCollection(user_id=user.id, name=data.name.strip())
    db.add(row)
    await db.commit()
    return {"id": row.id, "name": row.name}


@router.post("/assets", status_code=201)
async def upload_asset(file: UploadFile, db: DB, user: CurrentUser):
    row = await QuestionImportService(db).upload(file, user.id)
    return {
        "id": row.id,
        "filename": row.filename,
        "mime_type": row.mime_type,
        "size": row.size,
        "page_count": row.page_count,
    }


@router.get("/assets/{asset_id}")
async def download_asset(asset_id: str, db: DB, user: CurrentUser):
    row = await QuestionImportService(db).asset(asset_id, user.id)
    # PDFs are downloads: do not embed active PDF content in the application's origin.
    return FileResponse(
        row.path,
        media_type=row.mime_type,
        filename=row.filename,
        content_disposition_type="attachment" if row.mime_type == "application/pdf" else "inline",
        headers={"X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"},
    )


@router.post("/parse")
async def parse(data: ParseRequest, db: DB, user: CurrentUser):
    return await QuestionImportService(db, OpenAILLMClient()).parse(data, user.id)


async def save_response(data, db, user_id, question_id=None):
    row, duplicate = await QuestionRepository(db, user_id).save(data, question_id)
    if duplicate:
        return JSONResponse(
            status_code=409,
            content={
                "detail": "Nội dung này đã có trong thư viện. Xem đề đã lưu hoặc chọn lưu thêm bản mới.",
                "code": "duplicate_question",
                "duplicate": {"id": duplicate.id, "title": duplicate.title},
            },
        )
    return library_view(row)


@router.post("", status_code=201)
async def create_question(data: LibrarySave, db: DB, user: CurrentUser):
    return await save_response(data, db, user.id)


@router.get("/{question_id}")
async def get_question(question_id: str, db: DB, user: CurrentUser):
    row = await QuestionRepository(db, user.id).get(question_id)
    stats = await practice_stats(db, user.id, [row.id])
    return library_view(row, stats[row.id])


@router.put("/{question_id}")
async def update_question(question_id: str, data: LibrarySave, db: DB, user: CurrentUser):
    return await save_response(data, db, user.id, question_id)


@router.patch("/{question_id}")
async def organize(question_id: str, data: LibraryOrganize, db: DB, user: CurrentUser):
    repo = QuestionRepository(db, user.id)
    row = await repo.get(question_id, lock=True)
    doc = LibraryDocument.model_validate({**document_view(row), **data.model_dump(exclude_unset=True)})
    await repo.validate_links(doc)
    for key in data.model_fields_set:
        setattr(row, key, getattr(doc, key))
    await db.commit()
    return library_view(row)


@router.post("/{question_id}/duplicate", status_code=201)
async def duplicate_question(question_id: str, db: DB, user: CurrentUser):
    repo = QuestionRepository(db, user.id)
    row = await repo.get(question_id)
    doc = LibraryDocument.model_validate(document_view(row))
    doc.title = doc.title[:285] + " (bản sao)"
    return await save_response(LibrarySave(document=doc, save_duplicate=True), db, user.id)


@router.delete("/{question_id}", status_code=204)
async def delete_question(question_id: str, db: DB, user: CurrentUser):
    row = await QuestionRepository(db, user.id).get(question_id, lock=True)
    row.deleted_at = utcnow()
    await db.commit()


@router.post("/{question_id}/practice", status_code=201)
async def practice(question_id: str, data: LibraryPractice, db: DB, user: CurrentUser):
    return await LibraryPracticeService(db, OpenAILLMClient()).start(question_id, data, user.id)
