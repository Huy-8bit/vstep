import copy
import hashlib
from collections import Counter
from statistics import mean
from uuid import UUID

from sqlalchemy import func, select

from app.common.errors import AppError
from app.core.config import settings
from app.models.assessment import PronunciationPractice
from app.prompts.audio_assessment import AUDIO_ASSESSMENT_VERSION
from app.services.speaking_exam_service import SpeakingExamService, owned_speaking_answer
from app.services.speech_transcription_service import speech_cache_key, speech_lock


def practice_view(item):
    return {
        **{
            key: getattr(item, key)
            for key in (
                "id",
                "reference_text",
                "reference_hash",
                "source_answer_id",
                "source_issue_type",
                "status",
                "audio_duration_ms",
                "analysis",
                "pronunciation_score",
                "fluency_score",
                "audio_model",
                "prompt_version",
                "created_at",
                "updated_at",
            )
        },
        "audio_url": f"/api/v1/speaking/pronunciation/practices/{item.id}/audio" if item.audio_path else None,
    }


class PronunciationPracticeService:
    def __init__(self, db, storage, provider):
        self.db, self.storage, self.provider = db, storage, provider

    async def owned(self, identifier, user_id, lock=False):
        try:
            UUID(identifier)
        except (ValueError, TypeError):
            raise AppError(404, "Không tìm thấy lượt luyện.") from None
        query = select(PronunciationPractice).where(
            PronunciationPractice.id == identifier, PronunciationPractice.user_id == user_id
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        item = await self.db.scalar(query)
        if not item:
            raise AppError(404, "Không tìm thấy lượt luyện.")
        return item

    async def create(self, data, user_id):
        reference = " ".join(data.reference_text.split())
        if not reference:
            raise AppError(422, "Nhập từ hoặc câu tiếng Anh để luyện.")
        await speech_lock(self.db, f"pronunciation-create:{user_id}:{data.client_request_id}")
        existing = await self.db.scalar(
            select(PronunciationPractice).where(
                PronunciationPractice.user_id == user_id,
                PronunciationPractice.client_request_id == data.client_request_id,
            )
        )
        if existing:
            if existing.reference_text != reference or existing.source_answer_id != data.source_answer_id:
                raise AppError(409, "Yêu cầu đã dùng cho lượt luyện khác.")
            await self.db.commit()
            return existing
        if data.source_answer_id:
            answer = await owned_speaking_answer(self.db, data.source_answer_id, user_id)
            await SpeakingExamService(self.db, None, self.storage).can_review(answer, user_id)
        item = PronunciationPractice(
            user_id=user_id,
            reference_text=reference,
            reference_hash=hashlib.sha256(reference.casefold().encode()).hexdigest(),
            source_answer_id=data.source_answer_id,
            source_issue_type=data.source_issue_type,
            client_request_id=data.client_request_id,
        )
        self.db.add(item)
        await self.db.commit()
        return item

    async def upload(self, identifier, user_id, file):
        item = await self.owned(identifier, user_id, lock=True)
        # First accepted upload is immutable; duplicate retries must never replace it.
        if item.audio_path:
            await file.close()
            await self.db.commit()
            return item
        stored = await self.storage.store(file, user_id)
        item.audio_path, item.audio_hash = stored.path, stored.sha256
        item.audio_duration_ms, item.metrics, item.status = stored.duration_ms, stored.metrics, "RECORDED"
        try:
            await self.db.commit()
        except BaseException:
            self.storage.remove(stored.path)
            raise
        return item

    async def analyze(self, identifier, user_id):
        item = await self.owned(identifier, user_id, lock=True)
        if not item.audio_path:
            raise AppError(409, "Hãy lưu bản ghi trước khi phân tích.")
        key = speech_cache_key(
            item.audio_hash,
            item.reference_hash,
            settings.openai_speaking_audio_model,
            AUDIO_ASSESSMENT_VERSION,
            str(settings.audio_feedback_min_confidence),
        )
        if item.analysis_key == key and item.analysis is not None:
            await self.db.commit()
            await self.sync_learning(item, user_id)
            return item
        await speech_lock(self.db, f"pronunciation-analysis:{user_id}:{key}")
        cached = await self.db.scalar(
            select(PronunciationPractice)
            .where(
                PronunciationPractice.user_id == user_id,
                PronunciationPractice.analysis_key == key,
                PronunciationPractice.analysis.is_not(None),
            )
            .limit(1)
        )
        if cached:
            item.analysis = copy.deepcopy(cached.analysis)
        else:
            if not settings.openai_speaking_audio_model:
                raise AppError(503, "Phân tích phát âm đang tắt. Bản ghi đã được lưu.", "audio_disabled")
            assessment = await self.provider.assess(
                self.storage.resolve(item.audio_path),
                {"mode": "SCRIPTED_PRACTICE", "reference_text": item.reference_text, "metrics": item.metrics},
                user_id,
            )
            item.analysis = assessment.model_dump()
        item.analysis_key, item.status = key, "ANALYZED"
        item.pronunciation_score = item.analysis.get("pronunciation_score")
        item.fluency_score = item.analysis.get("fluency_score")
        item.audio_model, item.prompt_version = settings.openai_speaking_audio_model, AUDIO_ASSESSMENT_VERSION
        await self.db.commit()
        await self.sync_learning(item, user_id)
        return item

    async def sync_learning(self, item, user_id):
        import logging

        from app.learning.transfer import sync_pronunciation_learning

        try:
            await sync_pronunciation_learning(user_id, item.id)
        except Exception:
            logging.getLogger(__name__).exception("Pronunciation learning update deferred")

    async def history(self, user_id, reference_hash=None, offset=0, limit=20):
        query = select(PronunciationPractice).where(PronunciationPractice.user_id == user_id)
        if reference_hash:
            query = query.where(PronunciationPractice.reference_hash == reference_hash)
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = await self.db.scalars(
            query.order_by(PronunciationPractice.created_at.desc()).offset(offset).limit(limit)
        )
        return {"total": total, "items": [practice_view(item) for item in items]}

    async def progress(self, user_id):
        items = list(
            await self.db.scalars(
                select(PronunciationPractice)
                .where(PronunciationPractice.user_id == user_id, PronunciationPractice.status == "ANALYZED")
                .order_by(PronunciationPractice.created_at)
            )
        )
        by_reference, recurring = {}, Counter()
        for item in items:
            if item.pronunciation_score is not None:
                by_reference.setdefault(item.reference_hash, []).append(item)
            for issue in (item.analysis or {}).get("issues", []):
                recurring[(issue["type"], issue["target"].casefold())] += 1
        improved = []
        difficult = []
        for entries in by_reference.values():
            first, latest = entries[0], entries[-1]
            row = {
                "reference_text": latest.reference_text,
                "reference_hash": latest.reference_hash,
                "first_score": first.pronunciation_score,
                "latest_score": latest.pronunciation_score,
                "attempts": len(entries),
            }
            if len(entries) > 1 and latest.pronunciation_score > first.pronunciation_score:
                improved.append(row)
            if latest.pronunciation_score < 7:
                difficult.append(row)
        return {
            "attempts": len(items),
            "scored_attempts": sum(i.pronunciation_score is not None for i in items),
            "average_pronunciation": round(
                mean([i.pronunciation_score for i in items if i.pronunciation_score is not None]), 2
            )
            if any(i.pronunciation_score is not None for i in items)
            else None,
            "timeline": [
                {
                    "id": i.id,
                    "date": i.created_at,
                    "reference_text": i.reference_text,
                    "pronunciation": i.pronunciation_score,
                    "fluency": i.fluency_score,
                }
                for i in items
            ],
            "recurring_issues": [
                {"type": key[0], "target": key[1], "count": count} for key, count in recurring.most_common(10)
            ],
            "difficult_words": sorted(difficult, key=lambda r: r["latest_score"])[:10],
            "improved_words": sorted(
                improved, key=lambda r: r["latest_score"] - r["first_score"], reverse=True
            )[:10],
        }
