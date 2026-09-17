import hashlib
import random

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.llm.base import LLMClient
from app.models import WritingQuestion
from app.prompts.question_generator import QUESTION_GENERATOR_PROMPT_VERSION
from app.schemas.writing import TASK1_TYPES, TASK2_TYPES, TOPICS, QuestionRequest


def question_fingerprint(instruction: str) -> str:
    return hashlib.sha256(" ".join(instruction.lower().split()).encode()).hexdigest()


class QuestionGeneratorService:
    def __init__(self, db, llm: LLMClient):
        self.db = db
        self.llm = llm

    async def generate(self, request: QuestionRequest, user_id: str) -> WritingQuestion:
        if request.source == "SEED":
            query = select(WritingQuestion).where(
                WritingQuestion.task_type == request.task,
                WritingQuestion.source == "SEED",
                WritingQuestion.test_profile == request.test_profile,
            )
            if request.question_type != "random":
                query = query.where(WritingQuestion.question_type == request.question_type)
            if request.topic != "random":
                query = query.where(WritingQuestion.topic == request.topic)
            fresh = query.where(WritingQuestion.id.not_in(request.exclude_ids))
            question = await self.db.scalar(fresh.order_by(func.random()).limit(1))
            if not question:
                question = await self.db.scalar(query.order_by(func.random()).limit(1))
            if not question:
                raise AppError(
                    404,
                    "Chưa có đề mẫu với bộ lọc này. Hãy chọn Ngẫu nhiên hoặc sinh đề bằng AI.",
                    "no_seed_match",
                )
            return question
        payload = request.model_dump(exclude={"source", "exclude_ids"})
        if payload["question_type"] == "random":
            payload["question_type"] = random.choice(TASK1_TYPES if request.task == 1 else TASK2_TYPES)
        if payload["topic"] == "random":
            payload["topic"] = random.choice(TOPICS)
        payload["recent_prompts"] = list(
            await self.db.scalars(
                select(WritingQuestion.instruction)
                .where(WritingQuestion.task_type == request.task)
                .order_by(WritingQuestion.created_at.desc())
                .limit(20)
            )
        )
        result = await self.llm.generate_question(payload, user_id)
        question = WritingQuestion(
            task_type=result.task,
            **result.model_dump(exclude={"task"}),
            source="AI",
            fingerprint=question_fingerprint(result.instruction),
            prompt_version=QUESTION_GENERATOR_PROMPT_VERSION,
        )
        self.db.add(question)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(409, "AI đã tạo đề trùng. Hãy thử sinh đề khác.", "duplicate_question") from None
        return question
