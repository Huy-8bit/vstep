import hashlib
import random

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.common.test_profiles import ITEM_DIFFICULTY_BANDS, VSTEP_3_5
from app.common.words import count_words
from app.models.reading import ReadingExamSession, ReadingPassage, ReadingQuestion
from app.prompts.reading_question_generator import READING_GENERATOR_PROMPT_VERSION
from app.schemas.reading import READING_TOPICS, ReadingGenerateRequest
from app.services.reading_blueprint import READING_BLUEPRINT
from app.validators.quality import ReadingQuestionQualityValidator
from app.validators.questions import reject_near_duplicate
from app.vstep_reference.reading_blueprints import READING_TAXONOMY


def passage_from_generated(data, source="AI"):
    content = "\n\n".join(p.text for p in data.paragraphs)
    passage = ReadingPassage(
        title=data.title,
        topic=data.topic,
        test_profile=data.test_profile,
        internal_difficulty_band=data.internal_difficulty_band,
        content=content,
        paragraphs=[p.model_dump() for p in data.paragraphs],
        word_count=count_words(content),
        source=source,
        fingerprint=hashlib.sha256(content.strip().casefold().encode()).hexdigest(),
        prompt_version=READING_GENERATOR_PROMPT_VERSION,
        vocabulary_cache={},
        generation_diagnostics={
            "generator_version": "3.0.0",
            "validator_version": "3.0.0",
            "generation_model": None,
            "format_valid": True,
            "quality_valid": source == "SEED",
            "quality_method": "authored_synthetic_seed" if source == "SEED" else "pending",
            "source_blueprint": "reading_3.0.0",
            "validation_notes": [],
        },
    )
    passage.questions = [
        ReadingQuestion(**q.model_dump(), test_profile=data.test_profile) for q in data.questions
    ]
    return passage


class ReadingQuestionGeneratorService:
    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def bank(self, topic="random", user_id=None):
        visible = ReadingPassage.owner_id.is_(None) if user_id is None else or_(ReadingPassage.owner_id.is_(None), ReadingPassage.owner_id == user_id)
        query = select(ReadingPassage).where(visible).where(
            ReadingPassage.test_profile == VSTEP_3_5,
            ReadingPassage.generation_diagnostics["quality_valid"].as_boolean().is_(True),
            ReadingPassage.access_tier.in_(["FREE_TRIAL", "VIP"]),
            or_(ReadingPassage.owner_id == user_id, ReadingPassage.is_published.is_(True)) if user_id else ReadingPassage.is_published.is_(True),
        )
        if topic != "random":
            query = query.where(ReadingPassage.topic == topic)
        return list(await self.db.scalars(query))

    async def ordered_bank(self, topic, user_id):
        bank = await self.bank(topic, user_id)
        seen_groups = await self.db.scalars(
            select(ReadingExamSession.passage_ids).where(ReadingExamSession.user_id == user_id)
        )
        seen = {pid for group in seen_groups for pid in group}
        random.shuffle(bank)
        bank.sort(key=lambda p: p.id in seen)
        return bank

    async def generate(self, request: ReadingGenerateRequest, user_id, *, slot=None, plan=None, learning_focus=None, publish_global=False):
        if learning_focus and request.mode == "FULL_TEST":
            raise AppError(422, "Luyện điểm yếu chỉ áp dụng trong chế độ học.")
        # Only this service chooses internal item targets. Public requests never carry proficiency levels.
        bank = await self.ordered_bank("random" if request.mode == "FULL_TEST" else request.topic, user_id)
        if request.mode == "FULL_TEST":
            plan = plan if plan is not None else READING_BLUEPRINT.select(bank)
            if slot is None:
                missing = [s for s, p in zip(READING_BLUEPRINT.slots, plan) if p is None]
                slot = missing[0] if missing else random.choice(READING_BLUEPRINT.slots)
            band = slot.internal_difficulty_band
            generation_context = READING_BLUEPRINT.context(slot, plan)
        else:
            band = random.choice(ITEM_DIFFICULTY_BANDS)
            generation_context = {"practice_mode": request.mode}
        recent_sessions = await self.db.scalars(
            select(ReadingExamSession.passage_ids)
            .where(ReadingExamSession.user_id == user_id)
            .order_by(ReadingExamSession.created_at.desc())
            .limit(8)
        )
        ids = {pid for group in recent_sessions for pid in group}
        recent = list(
            await self.db.scalars(select(ReadingPassage).where(ReadingPassage.owner_id.is_(None)).where(ReadingPassage.id.in_(ids)).limit(20))
        )
        payload = request.model_dump()
        if learning_focus:
            payload["learning_focus"] = learning_focus
        companions = [p for p in (plan or []) if p]
        payload["recent_topics"] = list(
            dict.fromkeys([p.topic for p in companions] + request.recent_topics + [p.topic for p in recent])
        )[:20]
        payload["recent_titles"] = list(
            dict.fromkeys([p.title for p in companions] + request.recent_titles + [p.title for p in recent])
        )[:20]
        payload["internal_difficulty_band"] = band
        payload["generation_context"] = generation_context
        payload["taxonomy"] = READING_TAXONOMY
        if request.topic == "random" or request.mode == "FULL_TEST":
            payload["topic"] = random.choice(
                [t for t in READING_TOPICS if t not in payload["recent_topics"]] or READING_TOPICS
            )
        generated = await self.llm.generate_reading(payload, user_id)
        reject_near_duplicate(" ".join(p.text for p in generated.paragraphs), [p.content for p in bank[:30]])
        diagnostics = await ReadingQuestionQualityValidator().validate(self.llm, generated, user_id,
            practice_context={"mode": request.mode, "target_question_types": request.target_question_types, "question_count": request.question_count})
        diagnostics["source_blueprint"] = (
            "reading_full_3.0.0" if request.mode == "FULL_TEST" else "reading_practice_3.0.0"
        )
        passage = passage_from_generated(generated)
        passage.generation_diagnostics = diagnostics
        passage.owner_id = user_id if learning_focus or not publish_global else None
        passage.is_published = False
        passage.access_tier = "VIP"
        if learning_focus:
            passage.owner_id = user_id
            passage.generation_diagnostics = {**diagnostics, "learning_focus": learning_focus}
        if request.mode == "FULL_TEST":
            if not READING_BLUEPRINT.accepts(passage, slot):
                raise AppError(
                    502,
                    "Bài đọc chưa phù hợp vị trí trong đề; chưa lưu vào ngân hàng.",
                    "reading_slot_invalid",
                )
            lower, upper = generation_context["passage_word_range"]
            if not lower <= passage.word_count <= upper:
                raise AppError(
                    502,
                    "Bài đọc chưa khớp tổng độ dài của đề; chưa lưu vào ngân hàng.",
                    "reading_word_budget",
                )
            candidate_plan = list(plan)
            candidate_plan[slot.position - 1] = passage
            # Pending ORM object needs a stable identity for global uniqueness checks.
            from uuid import uuid4

            passage.id = str(uuid4())
            if all(candidate_plan) and not READING_BLUEPRINT.complete(candidate_plan):
                raise AppError(
                    502,
                    "Bộ đề chưa cân bằng số từ, chủ đề hoặc dạng câu; chưa lưu bài vừa sinh.",
                    "reading_global_balance",
                )
        self.db.add(passage)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise AppError(409, "Đề AI trùng nội dung đã có. Hãy tạo đề khác.", "duplicate_reading") from None
        return passage

    async def select(self, data, user_id):
        bank = await self.ordered_bank("random" if data.mode == "FULL_TEST" else data.topic, user_id)
        if data.mode == "FULL_TEST":
            plan = READING_BLUEPRINT.select(bank)
            missing = [p for p in plan if p is None]
            if missing:
                raise AppError(
                    409,
                    f"Bộ lọc còn thiếu {len(missing)} bài đọc để ghép đề VSTEP.3–5 có đủ độ phân hóa và dạng câu. Chọn chủ đề ngẫu nhiên hoặc bổ sung đề bằng AI.",
                    "reading_bank_insufficient",
                )
            if not READING_BLUEPRINT.complete(plan):
                raise AppError(
                    409,
                    "Ngân hàng chưa ghép được đề có 1900–2050 từ và đủ độ đa dạng. Hãy bổ sung đề hoặc chọn chủ đề ngẫu nhiên.",
                    "reading_global_balance",
                )
            return [(p, q) for p in plan for q in p.questions]
        if data.passage_id:
            bank = [p for p in bank if p.id == data.passage_id]
            if not bank:
                raise AppError(422, "Đề đã chọn không khớp chủ đề hoặc không có trong ngân hàng VSTEP.3–5.")
        if data.mode == "QUESTION_TYPE_PRACTICE":
            selected = [
                (p, q) for p in bank for q in p.questions if q.question_type == data.target_question_type
            ][:5]
            if selected:
                return selected
        else:
            count = 5 if data.mode == "QUICK_PRACTICE" else 10
            eligible = [p for p in bank if len(p.questions) >= count]
            if eligible:
                return [(eligible[0], q) for q in eligible[0].questions[:count]]
        if data.passage_id:
            raise AppError(422, "Bài đã chọn chưa có đủ câu hỏi phù hợp với chế độ luyện này.")
        raise AppError(409, "Bộ lọc chưa có đủ câu phù hợp. Chọn chủ đề ngẫu nhiên hoặc bổ sung đề bằng AI.", "reading_bank_empty")
