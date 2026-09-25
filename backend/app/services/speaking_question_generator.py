import hashlib
import json
import random

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.llm.base import LLMClient
from app.models.speaking import SpeakingExamSession, SpeakingQuestion
from app.prompts.speaking_part1_generator import SPEAKING_PART1_PROMPT_VERSION
from app.prompts.speaking_part2_generator import SPEAKING_PART2_PROMPT_VERSION
from app.prompts.speaking_part3_generator import SPEAKING_PART3_PROMPT_VERSION
from app.schemas.speaking import SPEAKING_TOPICS, SpeakingQuestionRequest
from app.validators.quality import validate_quality
from app.validators.questions import SpeakingQuestionValidator
from app.vstep_reference.generation_examples import SPEAKING_STYLE_EXAMPLES
from app.vstep_reference.speaking_blueprints import SPEAKING_BLUEPRINTS

SPEAKING_VERSIONS = {
    1: SPEAKING_PART1_PROMPT_VERSION,
    2: SPEAKING_PART2_PROMPT_VERSION,
    3: SPEAKING_PART3_PROMPT_VERSION,
}


def speaking_fingerprint(data: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                key: data.get(key)
                for key in (
                    "part",
                    "question_text",
                    "topic_sets",
                    "situation",
                    "options",
                    "suggested_ideas",
                    "follow_up_questions",
                )
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


class SpeakingQuestionGeneratorService:
    def __init__(self, db, llm: LLMClient):
        self.db, self.llm = db, llm

    async def generate(self, request: SpeakingQuestionRequest, user_id: str, *, learning_focus=None, trial_only=False, publish_global=False) -> SpeakingQuestion:
        if trial_only and (request.part != 1 or request.source == "AI"):
            raise AppError(403, "Lượt miễn phí dùng đề Speaking Part 1 có sẵn.", "VIP_REQUIRED")
        recent_sets = list(
            await self.db.scalars(
                select(SpeakingExamSession.question_set)
                .where(SpeakingExamSession.user_id == user_id)
                .order_by(SpeakingExamSession.created_at.desc())
                .limit(5)
            )
        )
        recent_ids = set(request.recent_question_ids)
        recent_topics = set(request.recent_topics)
        for question_set in recent_sets:
            for step in question_set:
                recent_ids.add(step["question_id"])
                recent_topics.add(step["topic_code"])
        query = select(SpeakingQuestion).where(SpeakingQuestion.owner_id.is_(None)).where(
            SpeakingQuestion.part == request.part, SpeakingQuestion.test_profile == request.test_profile,
            SpeakingQuestion.is_published.is_(True),
            SpeakingQuestion.access_tier.in_(["FREE_TRIAL"] if trial_only else ["FREE_TRIAL", "VIP"]),
        )
        if trial_only:
            query = query.where(SpeakingQuestion.available_for_free_trial.is_(True))
        if request.source != "AI":
            query = query.where(
                SpeakingQuestion.generation_diagnostics["quality_valid"].as_boolean().is_(True)
            )
            if request.source == "SEED":
                query = query.where(SpeakingQuestion.source == "SEED")
            if request.topic != "random":
                query = query.where(SpeakingQuestion.topic == request.topic)
            fresh = query.where(SpeakingQuestion.id.not_in(recent_ids))
            varied = (
                fresh.where(SpeakingQuestion.topic.not_in(recent_topics))
                if request.topic == "random"
                else fresh
            )
            for candidate in (varied, fresh, query):
                question = await self.db.scalar(candidate.order_by(func.random()).limit(1))
                if question:
                    return question
            raise AppError(
                404,
                "Chưa có đề mẫu với bộ lọc này. Chọn chủ đề ngẫu nhiên hoặc sinh đề AI.",
                "no_seed_match",
            )
        candidates = [t for t in SPEAKING_TOPICS if t not in recent_topics] or SPEAKING_TOPICS
        topic = random.choice(candidates) if request.topic == "random" else request.topic
        recent_rows = list(
            await self.db.scalars(
                select(SpeakingQuestion).where(SpeakingQuestion.owner_id.is_(None)).where(SpeakingQuestion.id.in_(recent_ids)).limit(30)
            )
        )
        recent = [q.question_text for q in recent_rows]
        payload = {
            "part": request.part,
            "topic": topic,
            "test_profile": request.test_profile,
            "recent_questions": recent,
            "recent_topic_sets": [q.topic_sets for q in recent_rows if q.part == 1],
            "recent_situations": [q.situation for q in recent_rows if q.part == 2],
            "recent_topics": list(recent_topics),
            "blueprint": SPEAKING_BLUEPRINTS[request.part],
            "style_example": SPEAKING_STYLE_EXAMPLES[request.part],
            "recent_complete_prompts": [
                " ".join([q.question_text, q.situation or "", *q.options, *q.suggested_ideas])
                if q.part != 1
                else " ".join(text for t in q.topic_sets for text in t["questions"])
                for q in recent_rows
            ],
        }
        if learning_focus:
            payload["learning_focus"] = learning_focus
        generated = await self.llm.generate_speaking_question(payload, user_id)
        SpeakingQuestionValidator().validate(generated, payload["recent_complete_prompts"])
        diagnostics = await validate_quality(self.llm, "SPEAKING", generated.model_dump(), user_id)
        diagnostics["source_blueprint"] = SPEAKING_BLUEPRINTS[request.part]["id"]
        data = generated.model_dump(exclude={"allow_own_idea"})
        question = SpeakingQuestion(
            owner_id=user_id if learning_focus or not publish_global else None,
            **data,
            source="AI",
            generation_diagnostics=diagnostics,
            is_published=False,
            access_tier="VIP",
            fingerprint=speaking_fingerprint(data),
            prompt_version=SPEAKING_VERSIONS[request.part],
        )
        if learning_focus:
            question.generation_diagnostics = {**diagnostics, "learning_focus": learning_focus}
        self.db.add(question)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(409, "Đề AI bị trùng. Hãy thử sinh đề khác.", "duplicate_question") from None
        return question
