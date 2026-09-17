import hashlib

from sqlalchemy import select

from app.common.errors import AppError
from app.core.config import settings
from app.models.reading import ReadingPassage
from app.prompts.reading_vocabulary_explanation import READING_VOCABULARY_PROMPT_VERSION
from app.services.reading_exam_service import ReadingExamService


class VocabularyService:
    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def explain(self, request, user_id):
        session = await ReadingExamService(self.db).get(request.session_id, user_id)
        if session.status == "IN_PROGRESS":
            raise AppError(409, "Giải thích từ vựng mở sau khi nộp bài Reading.", "reading_help_locked")
        if request.passage_id not in session.passage_ids:
            raise AppError(404, "Bài đọc không thuộc phiên của bạn.")
        passage = await self.db.scalar(
            select(ReadingPassage).where(ReadingPassage.id == request.passage_id).with_for_update()
        )
        paragraph = next((p for p in passage.paragraphs if p["id"] == request.paragraph_id), None)
        term = request.term.strip()
        if (
            not term
            or not paragraph
            or term.casefold() not in paragraph["text"].casefold()
            or len(term.split()) > 8
        ):
            raise AppError(422, "Chọn một từ hoặc cụm từ ngắn có trong đoạn văn.")
        key = hashlib.sha256(
            f"{request.paragraph_id}:{term.casefold()}:{settings.openai_model}:{READING_VOCABULARY_PROMPT_VERSION}".encode()
        ).hexdigest()
        if key in passage.vocabulary_cache:
            return passage.vocabulary_cache[key]
        result = await self.llm.explain_reading_vocabulary(
            {"title": passage.title, "paragraph": paragraph["text"], "term": term}, user_id
        )
        data = {**result.model_dump(), "term": term}
        passage.vocabulary_cache = {**passage.vocabulary_cache, key: data}
        await self.db.commit()
        return data
