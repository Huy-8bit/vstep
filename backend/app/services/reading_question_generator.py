import hashlib
import random

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.errors import AppError
from app.common.test_profiles import ITEM_DIFFICULTY_BANDS, VSTEP_3_5
from app.common.words import count_words
from app.core.config import settings
from app.models.reading import ReadingExamSession, ReadingPassage, ReadingQuestion
from app.prompts.reading_question_generator import READING_GENERATOR_PROMPT_VERSION
from app.schemas.reading import READING_TOPICS, ReadingGenerateRequest
from app.services.reading_blueprint import READING_BLUEPRINT


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
    )
    passage.questions = [
        ReadingQuestion(**q.model_dump(), test_profile=data.test_profile) for q in data.questions
    ]
    return passage


class ReadingQuestionGeneratorService:
    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def bank(self, topic="random"):
        query = select(ReadingPassage).where(ReadingPassage.test_profile == VSTEP_3_5)
        if topic != "random":
            query = query.where(ReadingPassage.topic == topic)
        return list(await self.db.scalars(query))

    async def ordered_bank(self, topic, user_id):
        bank = await self.bank(topic)
        seen_groups = await self.db.scalars(
            select(ReadingExamSession.passage_ids).where(ReadingExamSession.user_id == user_id)
        )
        seen = {pid for group in seen_groups for pid in group}
        random.shuffle(bank)
        bank.sort(key=lambda p: p.id in seen)
        return bank

    async def generate(self, request: ReadingGenerateRequest, user_id, *, slot=None, plan=None):
        # Only this service chooses internal item targets. Public requests never carry proficiency levels.
        bank = await self.ordered_bank(request.topic, user_id)
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
            await self.db.scalars(select(ReadingPassage).where(ReadingPassage.id.in_(ids)).limit(20))
        )
        payload = request.model_dump()
        companions = [p for p in (plan or []) if p]
        payload["recent_topics"] = list(
            dict.fromkeys([p.topic for p in companions] + request.recent_topics + [p.topic for p in recent])
        )[:20]
        payload["recent_titles"] = list(
            dict.fromkeys([p.title for p in companions] + request.recent_titles + [p.title for p in recent])
        )[:20]
        payload["internal_difficulty_band"] = band
        payload["generation_context"] = generation_context
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

    async def select(self, data, user_id):
        bank = await self.ordered_bank(data.topic, user_id)
        if data.mode == "FULL_TEST":
            plan = READING_BLUEPRINT.select(bank)
            missing = [
                (slot, i) for i, (slot, p) in enumerate(zip(READING_BLUEPRINT.slots, plan)) if p is None
            ]
            if missing and not settings.openai_api_key:
                raise AppError(
                    409,
                    f"Bộ lọc còn thiếu {len(missing)} bài đọc để ghép đề VSTEP.3–5 có đủ độ phân hóa và dạng câu. Chọn chủ đề ngẫu nhiên hoặc bổ sung đề bằng AI.",
                    "reading_bank_insufficient",
                )
            for slot, i in missing:
                plan[i] = await self.generate(
                    ReadingGenerateRequest(
                        mode="FULL_TEST", test_profile=data.test_profile, topic=data.topic
                    ),
                    user_id,
                    slot=slot,
                    plan=plan,
                )
                if not READING_BLUEPRINT.accepts(plan[i], slot):
                    raise AppError(502, "Đề AI chưa đáp ứng cấu trúc bài thi Reading. Hãy tạo lại.")
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
            count, targets = 5, [data.target_question_type]
        else:
            count = 5 if data.mode == "QUICK_PRACTICE" else 10
            targets = []
            eligible = [p for p in bank if len(p.questions) >= count]
            if eligible:
                return [(eligible[0], q) for q in eligible[0].questions[:count]]
        if data.passage_id:
            raise AppError(422, "Bài đã chọn chưa có đủ câu hỏi phù hợp với chế độ luyện này.")
        if not settings.openai_api_key:
            raise AppError(
                409,
                "Bộ lọc chưa có đủ câu phù hợp. Chọn chủ đề ngẫu nhiên hoặc bổ sung đề bằng AI.",
                "reading_bank_empty",
            )
        passage = await self.generate(
            ReadingGenerateRequest(
                mode=data.mode,
                test_profile=data.test_profile,
                topic=data.topic,
                question_count=count,
                target_question_types=targets,
            ),
            user_id,
        )
        return [(passage, q) for q in passage.questions]
