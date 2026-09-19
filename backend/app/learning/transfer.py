"""Record completion of drills evaluated by the existing skill/audio graders."""

from sqlalchemy import func, select

from app.db.base import utcnow
from app.models.learning import LearningExerciseAnswer, PersonalizedExercise, UserLearningEvent


async def record_transfer(db, user_id, transfer, correct, source_url, explanation, version=None):
    transfer.completed_at = utcnow()
    parent_id = transfer.content.get("source_exercise_id")
    index = transfer.content.get("source_item_index")
    exercise_id = parent_id or transfer.id
    dedup = f"exercise:{exercise_id}:{index if index is not None else 'transfer'}"
    event = await db.scalar(
        select(UserLearningEvent).where(
            UserLearningEvent.user_id == user_id, UserLearningEvent.dedup_key == dedup
        )
    )
    event = event or UserLearningEvent(
        user_id=user_id,
        skill=transfer.skill,
        concept_key=transfer.concept_key,
        source_exercise_id=exercise_id,
        dedup_key=dedup,
    )
    event.event_type = (
        "EXERCISE_CORRECT"
        if correct is True
        else "EXERCISE_INCORRECT"
        if correct is False
        else "EXERCISE_ATTEMPTED"
    )
    event.source_attempt_id = transfer.content.get("attempt_id")
    event.details = {
        "verified": correct is not None,
        "source_url": source_url,
        "source_version": version,
        "transfer_id": transfer.id,
    }
    db.add(event)
    if parent_id is not None and index is not None:
        parent = await db.scalar(
            select(PersonalizedExercise)
            .where(PersonalizedExercise.id == parent_id, PersonalizedExercise.user_id == user_id)
            .with_for_update()
        )
        if parent:
            row = await db.scalar(
                select(LearningExerciseAnswer).where(
                    LearningExerciseAnswer.exercise_id == parent_id,
                    LearningExerciseAnswer.item_index == index,
                )
            )
            row = row or LearningExerciseAnswer(
                user_id=user_id,
                exercise_id=parent_id,
                item_index=index,
                answer="Đã gửi bài ghi âm.",
                duration_seconds=0,
            )
            row.correct, row.feedback = (
                correct,
                {"explanation_vi": explanation, "source_url": source_url, "source_version": version},
            )
            db.add(row)
            await db.flush()
            count = await db.scalar(
                select(func.count())
                .select_from(LearningExerciseAnswer)
                .where(LearningExerciseAnswer.exercise_id == parent_id)
            )
            if count == len(parent.content["items"]):
                parent.completed_at = utcnow()


async def record_attempt_transfers(db, user_id, skill, attempt_id, data):
    rows = await db.scalars(
        select(PersonalizedExercise).where(
            PersonalizedExercise.user_id == user_id,
            PersonalizedExercise.exercise_type == "TRANSFER",
            PersonalizedExercise.content["attempt_id"].as_string() == attempt_id,
            PersonalizedExercise.content["target_skill"].as_string() == skill,
        )
    )
    for transfer in rows:
        relevant = [s for s in data["signals"] if s["concept_key"] == transfer.concept_key]
        correct = (
            False
            if any(s["outcome"] == "ERROR" for s in relevant)
            else True
            if any(s["outcome"] == "SUCCESS" for s in relevant)
            else None
        )
        explanation = (
            "Bài đã được chấm và có bằng chứng dùng đúng nội dung đang luyện."
            if correct is True
            else "Bài đã được chấm; nội dung đang luyện vẫn xuất hiện lỗi."
            if correct is False
            else "Đã hoàn thành bài và nhận phản hồi. Chưa có bằng chứng đủ cụ thể để xác nhận thành thạo nội dung này. Xem kết quả bài gốc."
        )
        await record_transfer(
            db, user_id, transfer, correct, data["source_url"], explanation, data["source_version"]
        )


async def sync_pronunciation_learning(user_id, pronunciation_id):
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.learning.aggregation import WeaknessAggregationService
    from app.learning.signals import profile_for
    from app.models.assessment import PronunciationPractice
    from app.services.speech_transcription_service import speech_lock

    async with SessionLocal() as db:
        await speech_lock(db, f"learning:{user_id}")
        item = await db.scalar(
            select(PronunciationPractice).where(
                PronunciationPractice.id == pronunciation_id, PronunciationPractice.user_id == user_id
            )
        )
        if not item or not item.analysis:
            return
        audio = item.analysis
        rows = list(
            await db.scalars(
                select(PersonalizedExercise).where(
                    PersonalizedExercise.user_id == user_id,
                    PersonalizedExercise.content["pronunciation_id"].as_string() == pronunciation_id,
                )
            )
        )
        for transfer in rows:
            trusted = (
                audio.get("available")
                and audio.get("speech_present")
                and audio.get("pronunciation_confidence", 0) >= settings.audio_feedback_min_confidence
                and (audio.get("reference_coverage") or 0) >= 0.8
            )
            correct = None
            if trusted and item.pronunciation_score is not None:
                correct = item.pronunciation_score >= 7 and not audio.get("issues")
            await record_transfer(
                db,
                user_id,
                transfer,
                correct,
                f"/speaking/pronunciation?id={item.id}",
                audio.get("pronunciation_summary_vi")
                or audio.get("reason_vi")
                or "Chưa đủ bằng chứng âm thanh.",
                item.analysis_key,
            )
        if rows:
            await db.flush()
            profile = await profile_for(db, user_id)
            profile.revision += 1
            await WeaknessAggregationService(db).aggregate(user_id)
        await db.commit()
