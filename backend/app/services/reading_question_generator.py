import hashlib
import random

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.common.words import count_words
from app.core.config import settings
from app.models.reading import ReadingExamSession, ReadingPassage, ReadingQuestion
from app.prompts.reading_question_generator import READING_GENERATOR_PROMPT_VERSION
from app.schemas.reading import READING_TOPICS, ReadingGenerateRequest


def passage_from_generated(data, source="AI"):
    content = "\n\n".join(p.text for p in data.paragraphs)
    passage = ReadingPassage(
        title=data.title,
        topic=data.topic,
        difficulty=data.difficulty,
        content=content,
        paragraphs=[p.model_dump() for p in data.paragraphs],
        word_count=count_words(content),
        source=source,
        fingerprint=hashlib.sha256(content.strip().casefold().encode()).hexdigest(),
        prompt_version=READING_GENERATOR_PROMPT_VERSION,
        vocabulary_cache={},
    )
    passage.questions = [
        ReadingQuestion(**q.model_dump(), difficulty=data.difficulty) for q in data.questions
    ]
    return passage


class ReadingQuestionGeneratorService:
    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def generate(self, request: ReadingGenerateRequest, user_id):
        recent_sessions = await self.db.scalars(
            select(ReadingExamSession.passage_ids)
            .where(ReadingExamSession.user_id == user_id)
            .order_by(ReadingExamSession.created_at.desc())
            .limit(8)
        )
        ids = {pid for group in recent_sessions for pid in group}
        recent = list(
            await self.db.scalars(select(ReadingPassage).where(ReadingPassage.id.in_(ids)).limit(20))
        )
        payload = request.model_dump()
        payload["recent_topics"] = list(set(request.recent_topics + [p.topic for p in recent]))[:20]
        payload["recent_titles"] = list(dict.fromkeys(request.recent_titles + [p.title for p in recent]))[:20]
        if request.topic == "random":
            payload["topic"] = random.choice(
                [t for t in READING_TOPICS if t not in payload["recent_topics"]] or READING_TOPICS
            )
        generated = await self.llm.generate_reading(payload, user_id)
        passage = passage_from_generated(generated)
        self.db.add(passage)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(409, "Đề AI trùng nội dung đã có. Hãy tạo đề khác.", "duplicate_reading") from None
        return passage

    async def bank(self, difficulty, topic="random"):
        query = select(ReadingPassage).where(ReadingPassage.difficulty == difficulty)
        if topic != "random":
            query = query.where(ReadingPassage.topic == topic)
        return list(await self.db.scalars(query))

    async def select(self, data, user_id):
        bank = await self.bank(data.difficulty, data.topic)
        seen_groups = await self.db.scalars(
            select(ReadingExamSession.passage_ids).where(ReadingExamSession.user_id == user_id)
        )
        seen = {pid for group in seen_groups for pid in group}
        random.shuffle(bank)
        bank.sort(key=lambda p: p.id in seen)
        if data.passage_id:
            bank = [p for p in bank if p.id == data.passage_id]
            if not bank:
                raise AppError(422, "Đề đã chọn không khớp chủ đề hoặc độ khó.")
        if data.mode == "QUESTION_TYPE_PRACTICE":
            selected = [
                (p, q) for p in bank for q in p.questions if q.question_type == data.target_question_type
            ][:5]
            # Use the available targeted bank without silently charging or repeating a question.
            if selected:
                return selected
            if not settings.openai_api_key:
                raise AppError(
                    409,
                    "Chưa có câu hỏi dạng này trong bộ lọc. Chọn B2 hoặc chủ đề ngẫu nhiên.",
                    "reading_bank_empty",
                )
            passage = await self.generate(
                ReadingGenerateRequest(
                    mode=data.mode,
                    difficulty=data.difficulty,
                    topic=data.topic,
                    question_count=5,
                    target_question_types=[data.target_question_type],
                ),
                user_id,
            )
            return [(passage, q) for q in passage.questions]
        count = 4 if data.mode == "FULL_TEST" else 1
        needed_questions = 5 if data.mode == "QUICK_PRACTICE" else 10
        bank = [p for p in bank if len(p.questions) >= needed_questions]
        while len(bank) < count:
            if not settings.openai_api_key:
                raise AppError(
                    409,
                    f"Bộ lọc này có {len(bank)}/{count} bài đọc cần thiết. Chọn B2/chủ đề ngẫu nhiên hoặc cấu hình OpenAI để bổ sung ngân hàng.",
                    "reading_bank_insufficient",
                )
            bank.append(
                await self.generate(
                    ReadingGenerateRequest(
                        mode=data.mode,
                        difficulty=data.difficulty, topic=data.topic, question_count=needed_questions
                    ),
                    user_id,
                )
            )
        return [(p, q) for p in bank[:count] for q in p.questions[:needed_questions]]
