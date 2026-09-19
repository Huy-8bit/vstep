import hashlib
import json
import re
import unicodedata

from sqlalchemy import select

from app.common.errors import AppError
from app.models.library import LibraryQuestion, LibraryRevision, QuestionCollection, QuestionImportFile
from app.schemas.library import LibraryDocument


def fingerprint(document: LibraryDocument):
    # Compare normalized exam content; keys and organization can be added independently.
    excluded = {
        "practice_asset_ids",
        "correct_answer",
        "answer_key_source",
        "answer_key_evidence",
        "explanation",
    }

    def normalize(value):
        if isinstance(value, str):
            return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().casefold()
        if isinstance(value, list):
            return [normalize(v) for v in value]
        if isinstance(value, dict):
            return {k: normalize(v) for k, v in value.items() if k not in excluded}
        return value

    content = json.dumps(normalize(document.content.model_dump()), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()


def document_view(row):
    return {key: getattr(row, key) for key in LibraryDocument.model_fields}


class QuestionRepository:
    def __init__(self, db, user_id):
        self.db, self.user_id = db, user_id

    async def get(self, question_id, *, lock=False, include_deleted=False):
        query = select(LibraryQuestion).where(
            LibraryQuestion.id == question_id, LibraryQuestion.user_id == self.user_id
        )
        if not include_deleted:
            query = query.where(LibraryQuestion.deleted_at.is_(None))
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        row = await self.db.scalar(query)
        if not row:
            raise AppError(404, "Không tìm thấy đề trong thư viện.")
        return row

    async def validate_links(self, doc):
        if doc.collection_id:
            collection = await self.db.get(QuestionCollection, doc.collection_id)
            if not collection or collection.user_id != self.user_id:
                raise AppError(404, "Không tìm thấy bộ sưu tập.")
        if doc.asset_ids:
            rows = list(
                await self.db.scalars(
                    select(QuestionImportFile.id).where(
                        QuestionImportFile.id.in_(doc.asset_ids), QuestionImportFile.user_id == self.user_id
                    )
                )
            )
            if set(rows) != set(doc.asset_ids):
                raise AppError(404, "Không tìm thấy tệp nguồn.")

    async def duplicate_of(self, doc, exclude_id=None):
        query = select(LibraryQuestion).where(
            LibraryQuestion.user_id == self.user_id,
            LibraryQuestion.deleted_at.is_(None),
            LibraryQuestion.fingerprint == fingerprint(doc),
        )
        if exclude_id:
            query = query.where(LibraryQuestion.id != exclude_id)
        return await self.db.scalar(query.order_by(LibraryQuestion.created_at).limit(1))

    async def save(self, data, question_id=None):
        doc = data.document
        await self.validate_links(doc)
        row = await self.get(question_id, lock=True) if question_id else None
        if row and data.expected_revision != row.revision:
            raise AppError(409, "Đề đã thay đổi ở tab khác. Mở lại đề để tránh ghi đè.", "revision_conflict")
        duplicate = await self.duplicate_of(doc, question_id)
        if duplicate and not data.save_duplicate:
            return None, duplicate
        if row:
            row.revision += 1
            for key, value in doc.model_dump().items():
                setattr(row, key, value)
            row.fingerprint = fingerprint(doc)
        else:
            row = LibraryQuestion(
                user_id=self.user_id, **doc.model_dump(), revision=1, fingerprint=fingerprint(doc)
            )
            self.db.add(row)
        await self.db.flush()
        self.db.add(LibraryRevision(question_id=row.id, revision=row.revision, document=doc.model_dump()))
        await self.db.commit()
        return row, None

    async def revision(self, row, revision):
        snapshot = await self.db.scalar(
            select(LibraryRevision).where(
                LibraryRevision.question_id == row.id, LibraryRevision.revision == revision
            )
        )
        if not snapshot:
            raise AppError(404, "Không tìm thấy phiên bản đề.")
        return LibraryDocument.model_validate(snapshot.document)
