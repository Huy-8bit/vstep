import hashlib
import random

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.llm.base import LLMClient
from app.models import WritingAttempt, WritingQuestion
from app.prompts.question_generator import QUESTION_GENERATOR_PROMPT_VERSION
from app.schemas.writing import TASK1_TYPES, TASK2_TYPES, TOPICS, QuestionRequest
from app.validators.quality import validate_quality
from app.validators.questions import WritingQuestionValidator
from app.vstep_reference.generation_examples import WRITING_STYLE_EXAMPLES
from app.vstep_reference.writing_blueprints import WRITING_BLUEPRINTS


def question_fingerprint(instruction: str) -> str:
    return hashlib.sha256(" ".join(instruction.lower().split()).encode()).hexdigest()


class QuestionGeneratorService:
    def __init__(self, db, llm: LLMClient):
        self.db, self.llm = db, llm

    async def generate(self, request: QuestionRequest, user_id: str) -> WritingQuestion:
        recent = list(
            await self.db.scalars(
                select(WritingQuestion)
                .join(WritingAttempt)
                .where(WritingAttempt.user_id == user_id, WritingQuestion.task_type == request.task)
                .order_by(WritingAttempt.created_at.desc())
                .limit(20)
            )
        )
        ids = set(request.exclude_ids) | {q.id for q in recent}
        recent_topics = {q.topic for q in recent[:6]}
        if request.source != "AI":
            query = select(WritingQuestion).where(
                WritingQuestion.task_type == request.task,
                WritingQuestion.test_profile == request.test_profile,
                WritingQuestion.generation_diagnostics["quality_valid"].as_boolean().is_(True),
            )
            if request.source == "SEED":
                query = query.where(WritingQuestion.source == "SEED")
            if request.question_type != "random":
                query = query.where(WritingQuestion.question_type == request.question_type)
            if request.topic != "random":
                query = query.where(WritingQuestion.topic == request.topic)
            fresh = query.where(WritingQuestion.id.not_in(ids))
            varied = (
                fresh.where(WritingQuestion.topic.not_in(recent_topics))
                if request.topic == "random"
                else fresh
            )
            for candidate in (varied, fresh, query):
                question = await self.db.scalar(candidate.order_by(func.random()).limit(1))
                if question:
                    return question
            raise AppError(
                404,
                "Ngân hàng chưa có đề đã kiểm duyệt cho bộ lọc này. Chọn Ngẫu nhiên hoặc tạo đề AI.",
                "no_seed_match",
            )
        payload = request.model_dump(exclude={"source", "exclude_ids"})
        if payload["question_type"] == "random":
            payload["question_type"] = random.choice(TASK1_TYPES if request.task == 1 else TASK2_TYPES)
        if payload["topic"] == "random":
            payload["topic"] = random.choice([t for t in TOPICS if t not in recent_topics] or TOPICS)
        bank_recent = list(
            await self.db.scalars(
                select(WritingQuestion)
                .where(WritingQuestion.task_type == request.task)
                .order_by(WritingQuestion.created_at.desc())
                .limit(15)
            )
        )
        payload.update(
            blueprint=WRITING_BLUEPRINTS[request.task],
            style_example=WRITING_STYLE_EXAMPLES[request.task],
            recent_prompts=[q.instruction + " " + (q.stimulus or "") for q in recent + bank_recent],
            recent_topics=list(recent_topics),
            recent_prompt_fingerprints=[q.fingerprint for q in recent],
        )
        result = await self.llm.generate_question(payload, user_id)
        WritingQuestionValidator().validate(result, payload["recent_prompts"])
        diagnostics = await validate_quality(self.llm, "WRITING", result.model_dump(), user_id)
        diagnostics["source_blueprint"] = WRITING_BLUEPRINTS[request.task]["id"]
        question = WritingQuestion(
            task_type=result.task,
            **result.model_dump(exclude={"task"}),
            source="AI",
            fingerprint=question_fingerprint(result.instruction + " " + result.stimulus),
            prompt_version=QUESTION_GENERATOR_PROMPT_VERSION,
            generation_diagnostics=diagnostics,
        )
        self.db.add(question)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(409, "AI đã tạo đề trùng. Hãy thử sinh đề khác.", "duplicate_question") from None
        return question
