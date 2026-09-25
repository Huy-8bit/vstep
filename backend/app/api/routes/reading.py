from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.api.reading_serializers import reading_passage_view, reading_result_view, reading_session_view
from app.common.errors import AppError
from app.core.config import settings
from app.llm.openai_client import OpenAILLMClient
from app.models.reading import ReadingPassage
from app.schemas.reading import (
    ReadingAnswerUpdate,
    ReadingBatchUpdate,
    ReadingGenerateRequest,
    ReadingMode,
    ReadingSessionCreate,
    VocabularyRequest,
)
from app.services.entitlements import EntitlementService
from app.services.reading_blueprint import READING_BLUEPRINT
from app.services.reading_exam_service import ReadingExamService
from app.services.reading_progress_service import ReadingProgressService
from app.services.reading_question_generator import ReadingQuestionGeneratorService
from app.services.vocabulary_service import VocabularyService

router = APIRouter(prefix="/reading", tags=["Reading"])


@router.get("/bank")
async def bank(db: DB, user: CurrentUser, topic: str = "random"):
    await EntitlementService(db).require(user, "READING_QUICK" if settings.free_reading_enabled else "READING")
    rows = await ReadingQuestionGeneratorService(db, OpenAILLMClient()).bank(topic, user.id)
    return {
        "ai_configured": bool(settings.openai_api_key),
        "test_profile": "VSTEP_3_5",
        "full_test_missing_passages": sum(p is None for p in READING_BLUEPRINT.select(rows)),
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "topic": p.topic,
                "test_profile": p.test_profile,
                "word_count": p.word_count,
                "question_count": len(p.questions),
                "question_types": [q.question_type for q in p.questions],
                "source": p.source,
            }
            for p in rows
        ],
    }


@router.post("/questions/generate")
async def generate(data: ReadingGenerateRequest, db: DB, user: CurrentUser):
    await EntitlementService(db).require(user, "READING")
    await EntitlementService(db).require(user, "AI_GENERATION", consume=True)
    return reading_passage_view(
        await ReadingQuestionGeneratorService(db, OpenAILLMClient()).generate(data, user.id, publish_global=user.role == "ADMIN")
    )


@router.get("/passages/{passage_id}")
async def passage(passage_id: str, db: DB, user: CurrentUser):
    await EntitlementService(db).require(user, "READING")
    row = await db.get(ReadingPassage, passage_id)
    if not row or row.owner_id not in (None, user.id) or (row.owner_id is None and (not row.is_published or row.access_tier == "INTERNAL")):
        raise AppError(404, "Không tìm thấy bài đọc.")
    return reading_passage_view(row)


@router.post("/sessions", status_code=201)
async def create(data: ReadingSessionCreate, db: DB, user: CurrentUser):
    decision = await EntitlementService(db).require(user, "READING_QUICK" if data.mode == "QUICK_PRACTICE" and settings.free_reading_enabled else "READING", consume=True)
    service = ReadingExamService(db, OpenAILLMClient())
    session = await service.create(data, user.id, access_source="ADMIN" if user.role == "ADMIN" else "FREE" if not decision.vip_expires_at else "VIP")
    return reading_session_view(session, await service.passages(session))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: DB, user: CurrentUser):
    service = ReadingExamService(db)
    session = await service.get(session_id, user.id)
    return reading_session_view(session, await service.passages(session))


@router.patch("/sessions/{session_id}/answers")
async def save(session_id: str, data: ReadingBatchUpdate, db: DB, user: CurrentUser):
    service = ReadingExamService(db)
    session = await service.save(session_id, user.id, data.answers)
    return reading_session_view(session, await service.passages(session))


@router.put("/sessions/{session_id}/answers/{question_id}")
async def save_one(session_id: str, question_id: str, data: ReadingAnswerUpdate, db: DB, user: CurrentUser):
    service = ReadingExamService(db)
    session = await service.save(session_id, user.id, {question_id: data})
    return reading_session_view(session, await service.passages(session))


@router.post("/sessions/{session_id}/submit")
async def submit(session_id: str, data: ReadingBatchUpdate, db: DB, user: CurrentUser):
    service = ReadingExamService(db)
    session = await service.submit(session_id, user.id, data.answers)
    return reading_result_view(session, await service.passages(session))


@router.get("/results/{session_id}")
async def result(session_id: str, db: DB, user: CurrentUser):
    service = ReadingExamService(db)
    session = await service.get(session_id, user.id)
    if session.status == "IN_PROGRESS":
        raise AppError(409, "Nộp bài Reading trước khi xem đáp án và bằng chứng.", "reading_result_locked")
    return reading_result_view(session, await service.passages(session))


@router.get("/history")
async def history(
    db: DB,
    user: CurrentUser,
    mode: ReadingMode | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return await ReadingProgressService(db).history(user.id, mode, offset, limit)


@router.get("/progress")
async def progress(db: DB, user: CurrentUser, mode: ReadingMode | None = None):
    return await ReadingProgressService(db).progress(user.id, mode)


@router.post("/vocabulary/explain")
async def vocabulary(data: VocabularyRequest, db: DB, user: CurrentUser):
    await EntitlementService(db).require(user, "VOCABULARY")
    return await VocabularyService(db, OpenAILLMClient()).explain(data, user.id)
