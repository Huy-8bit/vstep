from sqlalchemy import select

from app.common.errors import AppError
from app.learning import EXERCISE_VERSION
from app.learning.coaching import PersonalizedCoachService
from app.learning.taxonomy.reading import TYPES
from app.llm.routing import route_for
from app.models.learning import PersonalizedExercise
from app.schemas.api import ExamCreate
from app.schemas.reading import ReadingGenerateRequest, ReadingSessionCreate
from app.schemas.speaking import SpeakingQuestionRequest, SpeakingSessionCreate
from app.schemas.writing import QuestionRequest
from app.services.exam_service import ExamService
from app.services.question_generator import QuestionGeneratorService
from app.services.reading_exam_service import ReadingExamService
from app.services.reading_question_generator import ReadingQuestionGeneratorService
from app.services.speaking_exam_service import SpeakingExamService
from app.services.speaking_question_generator import SpeakingQuestionGeneratorService
from app.services.speech_transcription_service import speech_lock


class TargetedPracticeService:
    """Only learning modes; route through the established practice/recording/grading engines."""

    def __init__(self, db, llm):
        self.db, self.llm = db, llm

    async def start(self, identifier, user_id, data):
        from datetime import timedelta

        from app.db.base import utcnow
        from app.learning.analysis import owned_weakness

        await speech_lock(self.db, f"learning-target:{user_id}:{data.client_request_id}")
        row = await self.db.scalar(
            select(PersonalizedExercise).where(
                PersonalizedExercise.user_id == user_id,
                PersonalizedExercise.client_request_id == str(data.client_request_id),
            )
        )
        if row:
            if (
                row.weakness_id != identifier
                or row.exercise_type != "TRANSFER"
                or row.content.get("target_skill") != data.skill
                or row.content.get("source", "AI") != data.source
            ):
                raise AppError(409, "Yêu cầu đã dùng cho lượt luyện khác.")
            if row.content.get("url"):
                return row.content
            if row.content.get("status") == "PENDING" and row.updated_at > utcnow() - timedelta(minutes=10):
                raise AppError(
                    409,
                    "Đề đang được tạo. Hãy đợi một chút rồi thử lại cùng yêu cầu.",
                    "learning_generation_pending",
                )
        w = await owned_weakness(self.db, identifier, user_id)
        row = row or PersonalizedExercise(
            user_id=user_id,
            weakness_id=w.id,
            skill=w.skill,
            concept_key=w.concept_key,
            exercise_type="TRANSFER",
            version=EXERCISE_VERSION,
            model=route_for("learning_exercises").model,
            client_request_id=str(data.client_request_id),
        )
        row.content = {
            "status": "PENDING",
            "target_skill": data.skill,
            "source": data.source,
            "title": w.display_name_vi,
            "items": [],
            "source_exercise_id": data.exercise_id,
            "source_item_index": data.item_index,
        }
        self.db.add(row)
        await self.db.commit()
        row_id = row.id
        try:
            result = await self._perform(identifier, user_id, data)
        except Exception:
            await self.db.rollback()
            row = await self.db.get(PersonalizedExercise, row_id)
            row.content = {**row.content, "status": "FAILED"}
            await self.db.commit()
            raise
        row = await self.db.get(PersonalizedExercise, row_id)
        row.content = {**row.content, **result, "status": "READY"}
        await self.db.commit()
        return result

    async def _perform(self, identifier, user_id, data):
        coach = PersonalizedCoachService(self.db, self.llm)
        w, context = await coach.context(identifier, user_id)
        if w.skill not in {"CROSS", data.skill}:
            raise AppError(422, "Nội dung không thuộc kỹ năng đã chọn.")
        focus = {
            "concept_key": w.concept_key,
            "label_vi": w.display_name_vi,
            "learning_mode_only": True,
            "instruction": "Create a natural practice task that provides opportunities to use this concept. No hints or answers inside the question. Keep the selected part structure.",
        }
        source_exercise = None
        if data.exercise_id:
            source_exercise = await coach.owned_exercise(data.exercise_id, user_id)
            if (
                source_exercise.weakness_id != w.id
                or data.item_index is None
                or data.item_index >= len(source_exercise.content["items"])
            ):
                raise AppError(422, "Câu luyện không thuộc nội dung này.")
            item = source_exercise.content["items"][data.item_index]
            focus["drill"] = {
                k: item.get(k) for k in ("kind", "instruction_vi", "text", "target_words", "seconds")
            }
        if w.category == "PRONUNCIATION":
            targets = [e["original"] for e in context["evidence"] if e["original"]]
            if source_exercise:
                targets = item.get("target_words") or targets
            from app.schemas.audio_assessment import PronunciationCreate
            from app.services.pronunciation_practice_service import PronunciationPracticeService

            practice = await PronunciationPracticeService(self.db, None, None).create(
                PronunciationCreate(
                    reference_text=" ".join(dict.fromkeys(targets))[:500],
                    client_request_id=str(data.client_request_id),
                    source_issue_type=w.concept_key[:40],
                ),
                user_id,
            )
            result = {
                "url": f"/speaking/pronunciation?id={practice.id}",
                "pronunciation_id": practice.id,
                "skill": "SPEAKING",
                "target_skill": "SPEAKING",
            }
        elif data.skill == "WRITING":
            part = data.part or 2
            if part not in (1, 2):
                raise AppError(422, "Writing chỉ có Task 1 và Task 2.")
            q = await QuestionGeneratorService(self.db, self.llm).generate(
                QuestionRequest(task=part, source="AI"), user_id, learning_focus=focus
            )
            session = await ExamService(self.db, self.llm).create(
                ExamCreate(mode=f"TASK{part}", question_ids=[q.id], timed=False), user_id
            )
            result = {
                "url": f"/exam?id={session.id}",
                "attempt_id": session.attempts[0].id,
                "skill": "WRITING",
                "target_skill": data.skill,
            }
        elif data.skill == "SPEAKING":
            part = data.part or (
                2 if w.concept_key in {"POOR_COMPARISON", "ALTERNATIVES_NOT_REJECTED"} else 3
            )
            q = await SpeakingQuestionGeneratorService(self.db, self.llm).generate(
                SpeakingQuestionRequest(part=part, source="AI"), user_id, learning_focus=focus
            )
            session = await SpeakingExamService(self.db, self.llm, None).create(
                SpeakingSessionCreate(mode=f"PART{part}", question_id=q.id), user_id
            )
            if source_exercise and item["kind"] in {
                "SHORT_ANSWER",
                "SENTENCE_EXPANSION",
                "TIMED_RESPONSE",
                "REUSE_VOCABULARY",
                "PART3_DEVELOPMENT",
            }:
                session.question_set = session.question_set[:1]
                if item.get("seconds"):
                    session.question_set = [
                        {**step, "practice_seconds": item["seconds"]} for step in session.question_set
                    ]
                await self.db.commit()
            result = {
                "url": f"/speaking/exam?id={session.id}",
                "attempt_id": session.id,
                "skill": "SPEAKING",
                "target_skill": data.skill,
            }
        else:
            qtype = next((k for k, v in TYPES.items() if v[0] == w.concept_key), None)
            if not qtype:
                raise AppError(422, "Chưa có loại câu Reading tương ứng.")
            if data.source == "BANK":
                from app.models.reading import ReadingExamSession
                from app.services.reading_scoring_service import trusted_key

                bank = await ReadingQuestionGeneratorService(self.db, self.llm).ordered_bank(
                    "random", user_id
                )
                seen_groups = await self.db.scalars(
                    select(ReadingExamSession.question_ids).where(ReadingExamSession.user_id == user_id)
                )
                seen = {qid for group in seen_groups for qid in group}
                selected = [
                    (p, q) for p in bank for q in p.questions if q.question_type == qtype and trusted_key(q)
                ]
                selected.sort(key=lambda pair: pair[1].id in seen)
                if len(selected) < 10:
                    raise AppError(
                        409,
                        "Ngân hàng chưa đủ 10 câu loại này. Hãy chọn tạo bộ AI mới.",
                        "target_bank_insufficient",
                    )
                session = await ReadingExamService(self.db, self.llm).create(
                    ReadingSessionCreate(
                        mode="QUESTION_TYPE_PRACTICE", target_question_type=qtype, timed=False
                    ),
                    user_id,
                    selection=selected[:10],
                )
                return {
                    "url": f"/reading/exam?id={session.id}",
                    "attempt_id": session.id,
                    "skill": "READING",
                    "target_skill": "READING",
                    "source": "BANK",
                }
            # Two short passages give ten independent opportunities without forcing ten
            # similar inferences about one text. The full-test blueprint is untouched.
            passages = []
            for _ in range(2):
                passages.append(
                    await ReadingQuestionGeneratorService(self.db, self.llm).generate(
                        ReadingGenerateRequest(
                            mode="QUESTION_TYPE_PRACTICE",
                            question_count=5,
                            target_question_types=[qtype],
                            recent_titles=[p.title for p in passages],
                            recent_topics=[p.topic for p in passages],
                        ),
                        user_id,
                        learning_focus=focus,
                    )
                )
            session = await ReadingExamService(self.db, self.llm).create(
                ReadingSessionCreate(mode="QUESTION_TYPE_PRACTICE", target_question_type=qtype, timed=False),
                user_id,
                selection=[(passage, q) for passage in passages for q in passage.questions],
            )
            result = {
                "url": f"/reading/exam?id={session.id}",
                "attempt_id": session.id,
                "skill": "READING",
                "target_skill": data.skill,
            }
        return result
