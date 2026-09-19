import hashlib
import json
import re
from collections import Counter
from datetime import timedelta

from sqlalchemy import func, select

from app.common.errors import AppError
from app.core.config import settings
from app.db.base import utcnow
from app.llm.routing import route_for
from app.models import ExamSession, WritingAttempt, WritingError, WritingGrading
from app.models.reading import ReadingPassage
from app.models.speaking import SpeakingError, SpeakingGrading
from app.models.vocabulary import (
    UserVocabularyItem,
    VocabularyItemSource,
    VocabularyRecommendationBatch,
    VocabularyReview,
)
from app.prompts.vocabulary_coach import VOCABULARY_COACH_VERSION
from app.repositories.writing import owned_attempt
from app.services.reading_exam_service import ReadingExamService
from app.services.speaking_exam_service import owned_speaking_session
from app.services.speech_transcription_service import speech_lock


def canonical_topic(value):
    return {
        "transportation": "transport",
        "travel": "tourism",
        "career": "work",
        "study": "education",
        "social_activities": "community",
    }.get(value, value)


def normalized(value):
    return " ".join(re.findall(r"[\w]+", value.casefold()))


def validate_recommendations(result, payload):
    mode = payload["mode"]
    if mode in {"WRITING", "SPEAKING"} and not 5 <= sum(i.source_type == "TOPIC" for i in result.items) <= 8:
        raise ValueError("Select five to eight useful topic items")
    if mode == "READING_SELECTED" and len(result.items) != 1:
        raise ValueError("Selected Reading term needs one contextual item")
    if mode == "READING" and len(result.items) != 5:
        raise ValueError("Recommend five passage items")
    originals = [payload["source_text"], *[e["original"] for e in payload["recurring_errors"]]]
    if len({normalized(i.phrase) for i in result.items}) != len(result.items):
        raise ValueError("Avoid duplicate learning phrases")
    for item in result.items:
        if item.user_original and not any(item.user_original in text for text in originals):
            raise ValueError("Vocabulary must quote actual source content")
        if item.source_type == "REPEATED_ERROR" and not any(
            e["count"] >= 2 and item.user_original and item.user_original in e["original"]
            for e in payload["recurring_errors"]
        ):
            raise ValueError("Repeated errors require genuine historical occurrences")
        if item.source_type in {"UNNATURAL_EXPRESSION", "SPOKEN_EXPRESSION"} and (
            not item.user_original or not item.better_version
        ):
            raise ValueError("Corrections need original evidence and an improved expression")
        if mode.startswith("READING"):
            if (
                item.source_type != "READING_CONTEXT"
                or item.phrase.casefold() not in payload["source_text"].casefold()
                or not item.user_original
            ):
                raise ValueError("Reading vocabulary must be present in the actual passage")
            if mode == "READING_SELECTED" and normalized(item.phrase) != normalized(payload["selected_term"]):
                raise ValueError("Preserve the learner's selected phrase")


def item_view(item):
    return {
        key: getattr(item, key)
        for key in (
            "id",
            "headword",
            "phrase",
            "part_of_speech",
            "meaning_vi",
            "meaning_in_context_vi",
            "register",
            "collocations",
            "common_patterns",
            "source_skill",
            "source_attempt_id",
            "source_topic",
            "user_original_text",
            "improved_text",
            "example_sentence",
            "why_learn_this_vi",
            "issue_type",
            "priority",
            "mastery_level",
            "review_count",
            "correct_review_count",
            "last_reviewed_at",
            "next_review_at",
            "created_at",
            "updated_at",
        )
    }


def review_view(review):
    return {
        "id": review.id,
        "item_id": review.item_id,
        "kind": review.kind,
        "prompt": review.prompt,
        "answer": review.answer,
        "correct": review.correct,
        "feedback": review.feedback,
        "assessed_at": review.assessed_at,
    }


class VocabularyCoachService:
    def __init__(self, db, llm=None):
        self.db, self.llm = db, llm

    async def recurring_errors(self, user_id):
        writing = (
            await self.db.execute(
                select(
                    WritingError.category, WritingError.subtype, WritingError.original_text, WritingAttempt.id
                )
                .join(WritingGrading, WritingError.grading_id == WritingGrading.id)
                .join(WritingAttempt, WritingGrading.attempt_id == WritingAttempt.id)
                .where(
                    WritingAttempt.user_id == user_id,
                    WritingError.category.in_(
                        ["vocabulary", "word_choice", "collocation", "register", "grammar"]
                    ),
                )
            )
        ).all()
        speaking = (
            await self.db.execute(
                select(
                    SpeakingError.category,
                    SpeakingError.subtype,
                    SpeakingError.original,
                    SpeakingGrading.session_id,
                )
                .join(SpeakingGrading, SpeakingError.grading_id == SpeakingGrading.id)
                .where(
                    SpeakingGrading.user_id == user_id,
                    SpeakingGrading.session_id.is_not(None),
                    SpeakingError.category.in_(["vocabulary", "grammar"]),
                )
            )
        ).all()
        occurrences, labels = {}, {}
        for category, subtype, original, attempt in [*writing, *speaking]:
            if category == "grammar" and not any(
                key in subtype.casefold() for key in ("count", "plural", "word_form")
            ):
                continue
            if not original.strip():
                continue
            label = f"{category} {subtype}".casefold()
            issue = next(
                (
                    kind
                    for needle, kind in (
                        ("collocation", "collocation"),
                        ("count", "countability"),
                        ("plural", "countability"),
                        ("word_form", "word_form"),
                        ("register", "register"),
                    )
                    if needle in label
                ),
                "word_choice",
            )
            key = (issue, normalized(original))
            occurrences.setdefault(key, set()).add(attempt)
            labels[key] = original
        return [
            {"issue_type": key[0], "original": labels[key], "count": len(attempts)}
            for key, attempts in sorted(occurrences.items(), key=lambda pair: -len(pair[1]))
        ][:30]

    async def source_context(self, request, user_id):
        skill, identifier = request.source_skill, request.source_attempt_id
        if skill == "WRITING":
            attempt = await owned_attempt(self.db, identifier, user_id)
            exam = await self.db.get(ExamSession, attempt.exam_session_id)
            if exam.status == "IN_PROGRESS" or not attempt.grading:
                raise AppError(409, "Từ vựng mở sau khi nộp và chấm bài Writing.", "vocabulary_locked")
            q = attempt.question
            context = {
                "source_text": attempt.answer,
                "topic": q.topic,
                "task": attempt.task_type,
                "question": "\n".join(filter(None, [q.instruction, q.stimulus, q.response_instruction])),
                "observed_suggestions": attempt.grading.vocabulary_suggestions,
                "observed_errors": [
                    {
                        "original": e.original_text,
                        "corrected": e.corrected_text,
                        "category": e.category,
                        "subtype": e.subtype,
                    }
                    for e in attempt.grading.errors
                ],
                "grading_version": attempt.grading.grader_version,
                "exam_mode": exam.mode,
            }
        elif skill == "SPEAKING":
            session = await owned_speaking_session(self.db, identifier, user_id)
            if session.status == "IN_PROGRESS" or not session.grading:
                raise AppError(
                    409, "Từ vựng mở sau khi hoàn thành và chấm phiên Speaking.", "vocabulary_locked"
                )
            context = {
                "source_text": "\n".join(a.transcript or "" for a in session.answers),
                "topic": session.question_set[0]["topic_code"],
                "questions": session.question_set,
                "observed_suggestions": session.grading.vocabulary_suggestions,
                "observed_errors": [
                    {
                        "original": e.original,
                        "corrected": e.corrected,
                        "category": e.category,
                        "subtype": e.subtype,
                    }
                    for e in session.grading.errors
                    if e.category in {"vocabulary", "grammar"}
                ],
                "grading_version": session.grading.prompt_version,
                "exam_mode": session.mode,
            }
        else:
            session = await ReadingExamService(self.db).get(identifier, user_id)
            if session.status == "IN_PROGRESS":
                raise AppError(409, "Nộp bài Reading trước khi học hoặc lưu từ vựng.", "vocabulary_locked")
            if request.passage_id and request.passage_id not in session.passage_ids:
                raise AppError(404, "Bài đọc không thuộc phiên của bạn.")
            passage_ids = [request.passage_id] if request.passage_id else session.passage_ids
            passages = list(
                await self.db.scalars(select(ReadingPassage).where(ReadingPassage.id.in_(passage_ids)))
            )
            source = "\n\n".join(p.content for p in passages)
            if request.term:
                if not request.passage_id or not request.paragraph_id:
                    raise AppError(422, "Chọn một từ trong đoạn văn cụ thể.")
                paragraph = next((p for p in passages[0].paragraphs if p["id"] == request.paragraph_id), None)
                term = request.term.strip()
                if (
                    not paragraph
                    or not term
                    or not re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", paragraph["text"], re.I)
                    or len(term.split()) > 8
                ):
                    raise AppError(422, "Từ/cụm từ phải có trong đoạn văn đã chọn.")
                source = paragraph["text"]
            context = {
                "source_text": source,
                "topic": passages[0].topic,
                "passage_id": request.passage_id,
                "paragraph_id": request.paragraph_id,
                "selected_term": request.term,
                "exam_mode": session.mode,
            }
        context["topic"] = canonical_topic(context["topic"])
        context["mode"] = "READING_SELECTED" if skill == "READING" and request.term else skill
        context["recurring_errors"] = [e for e in await self.recurring_errors(user_id) if e["count"] >= 2]
        return context

    async def recommend(self, request, user_id, generate=True):
        context = await self.source_context(request, user_id)
        return await self._recommend_context(request, context, user_id, generate)

    async def prepare_writing(self, attempt, work, user_id):
        # Internal pipeline only: scores have been calibrated; public access still requires completed grading.
        from app.prompts.writing_analysis import WRITING_GRADER_VERSION
        from app.schemas.vocabulary_coach import VocabularyRecommendationRequest

        exam = await self.db.get(ExamSession, attempt.exam_session_id)
        if exam.status == "IN_PROGRESS":
            raise AppError(409, "Nộp bài trước khi học từ vựng.")
        q = attempt.question
        context = {
            "source_text": attempt.answer,
            "topic": canonical_topic(q.topic),
            "task": attempt.task_type,
            "question": "\n".join(filter(None, [q.instruction, q.stimulus, q.response_instruction])),
            "observed_suggestions": work["feedback"]["vocabulary_suggestions"],
            "observed_errors": work["analysis"]["evidence"]["errors"],
            "grading_version": WRITING_GRADER_VERSION,
            "exam_mode": exam.mode,
            "mode": "WRITING",
            "recurring_errors": [e for e in await self.recurring_errors(user_id) if e["count"] >= 2],
        }
        request = VocabularyRecommendationRequest(source_skill="WRITING", source_attempt_id=attempt.id)
        return await self._recommend_context(request, context, user_id)

    async def _recommend_context(self, request, context, user_id, generate=True):
        key = hashlib.sha256(
            json.dumps(
                {
                    "request": request.model_dump(),
                    "context": {
                        k: v
                        for k, v in context.items()
                        if k not in {"recurring_errors", "observed_errors", "observed_suggestions"}
                    },
                    "model": route_for("vocabulary_coach").identity,
                    "version": VOCABULARY_COACH_VERSION,
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        await speech_lock(self.db, f"vocabulary-batch:{user_id}:{key}")
        batch = await self.db.scalar(
            select(VocabularyRecommendationBatch).where(
                VocabularyRecommendationBatch.user_id == user_id,
                VocabularyRecommendationBatch.cache_key == key,
            )
        )
        if not batch and generate:
            result = await self.llm.vocabulary_coach(context, user_id)
            validate_recommendations(result, context)
            batch = VocabularyRecommendationBatch(
                user_id=user_id,
                source_skill=request.source_skill,
                source_attempt_id=request.source_attempt_id,
                source_topic=context["topic"],
                cache_key=key,
                items=result.model_dump()["items"],
                model=route_for("vocabulary_coach").model,
                prompt_version=VOCABULARY_COACH_VERSION,
            )
            self.db.add(batch)
            await self.db.flush()
        if not batch:
            await self.db.commit()
            return {"batch_id": None, "items": []}
        saved = dict(
            (
                await self.db.execute(
                    select(VocabularyItemSource.item_index, VocabularyItemSource.item_id).where(
                        VocabularyItemSource.batch_id == batch.id
                    )
                )
            ).all()
        )
        response = {
            "batch_id": batch.id,
            "source_skill": batch.source_skill,
            "source_topic": batch.source_topic,
            "items": [
                {
                    **{
                        k: v
                        for k, v in item.items()
                        if k not in {"collocation_distractors", "accepted_phrases"}
                    },
                    "index": i,
                    "saved_item_id": saved.get(i),
                }
                for i, item in enumerate(batch.items)
            ],
        }
        await self.db.commit()
        return response

    async def save(self, data, user_id):
        batch = await self.db.scalar(
            select(VocabularyRecommendationBatch).where(
                VocabularyRecommendationBatch.id == data.batch_id,
                VocabularyRecommendationBatch.user_id == user_id,
            )
        )
        if not batch or data.item_index >= len(batch.items):
            raise AppError(404, "Không tìm thấy gợi ý từ vựng.")
        value = batch.items[data.item_index]
        fingerprint = hashlib.sha256(
            f"{normalized(value['phrase'])}:{normalized(value['meaning_vi'])}:{value['register']}".encode()
        ).hexdigest()
        await speech_lock(self.db, f"vocabulary-save:{user_id}:{fingerprint}")
        item = await self.db.scalar(
            select(UserVocabularyItem).where(
                UserVocabularyItem.user_id == user_id, UserVocabularyItem.fingerprint == fingerprint
            )
        )
        if not item:
            item = UserVocabularyItem(
                user_id=user_id,
                fingerprint=fingerprint,
                **{
                    key: value[key]
                    for key in (
                        "headword",
                        "phrase",
                        "part_of_speech",
                        "meaning_vi",
                        "meaning_in_context_vi",
                        "register",
                        "collocations",
                        "common_patterns",
                        "example_sentence",
                        "why_learn_this_vi",
                        "issue_type",
                        "priority",
                    )
                },
                source_skill=batch.source_skill,
                source_attempt_id=batch.source_attempt_id,
                source_topic=batch.source_topic,
                user_original_text=value["user_original"] or None,
                improved_text=value["better_version"] or None,
                exercise_data={
                    key: value[key]
                    for key in ("collocation_distractors", "accepted_phrases", "natural_options")
                },
                next_review_at=utcnow(),
            )
            self.db.add(item)
            await self.db.flush()
        existing = await self.db.scalar(
            select(VocabularyItemSource).where(
                VocabularyItemSource.batch_id == batch.id, VocabularyItemSource.item_index == data.item_index
            )
        )
        if not existing:
            self.db.add(
                VocabularyItemSource(
                    item_id=item.id,
                    batch_id=batch.id,
                    item_index=data.item_index,
                    source_skill=batch.source_skill,
                    source_attempt_id=batch.source_attempt_id,
                    source_topic=batch.source_topic,
                )
            )
        await self.db.commit()
        return item_view(item)

    async def owned_item(self, identifier, user_id, lock=False):
        query = select(UserVocabularyItem).where(
            UserVocabularyItem.id == identifier, UserVocabularyItem.user_id == user_id
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        item = await self.db.scalar(query)
        if not item:
            raise AppError(404, "Không tìm thấy mục từ vựng.")
        return item

    async def list_items(self, user_id, section, skill, topic, offset, limit, search=""):
        query = select(UserVocabularyItem).where(UserVocabularyItem.user_id == user_id)
        if section == "DUE":
            query = query.where(UserVocabularyItem.next_review_at <= utcnow())
        elif section == "LEARNING":
            query = query.where(UserVocabularyItem.mastery_level.in_(["LEARNING", "FAMILIAR"]))
        elif section in {"NEW", "MASTERED"}:
            query = query.where(UserVocabularyItem.mastery_level == section)
        if skill:
            query = query.where(UserVocabularyItem.source_skill == skill)
        if topic:
            query = query.where(UserVocabularyItem.source_topic == canonical_topic(topic))
        if search:
            query = query.where(UserVocabularyItem.phrase.ilike(f"%{search[:100]}%"))
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = await self.db.scalars(
            query.order_by(
                UserVocabularyItem.next_review_at.asc().nullsfirst(), UserVocabularyItem.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )
        return {"total": total, "items": [item_view(item) for item in items]}

    async def history(self, user_id, offset, limit):
        query = (
            select(VocabularyReview, UserVocabularyItem.phrase)
            .join(UserVocabularyItem, VocabularyReview.item_id == UserVocabularyItem.id)
            .where(VocabularyReview.user_id == user_id, VocabularyReview.assessed_at.is_not(None))
        )
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        rows = (
            await self.db.execute(
                query.order_by(VocabularyReview.assessed_at.desc()).offset(offset).limit(limit)
            )
        ).all()
        return {"total": total, "items": [{**review_view(r), "phrase": phrase} for r, phrase in rows]}

    async def progress(self, user_id):
        items = list(
            await self.db.scalars(select(UserVocabularyItem).where(UserVocabularyItem.user_id == user_id))
        )
        counts = Counter(i.mastery_level for i in items)
        reviews = list(
            await self.db.scalars(
                select(VocabularyReview)
                .where(VocabularyReview.user_id == user_id, VocabularyReview.assessed_at.is_not(None))
                .order_by(VocabularyReview.assessed_at)
            )
        )
        by_id = {i.id: i for i in items}
        topics = Counter(by_id[r.item_id].source_topic for r in reviews if r.item_id in by_id)
        issue_groups = {}
        for r in reviews:
            if r.item_id in by_id and r.correct is not None:
                issue_groups.setdefault(by_id[r.item_id].issue_type, []).append(bool(r.correct))
        trends = []
        for issue, values in issue_groups.items():
            first, recent = values[:5], values[-5:]
            rate = round(sum(recent) / len(recent) * 100)
            trend = (
                "improving"
                if len(values) >= 6 and rate > sum(first) / len(first) * 100
                else "needs_practice"
                if rate < 70
                else "steady"
            )
            trends.append(
                {"issue_type": issue, "reviews": len(values), "recent_accuracy": rate, "trend": trend}
            )
        return {
            "total": len(items),
            "learned": sum(i.review_count > 0 for i in items),
            "mastered": counts["MASTERED"],
            "mastery": dict(counts),
            "due": sum(i.next_review_at is not None and i.next_review_at <= utcnow() for i in items),
            "reviews": len(reviews),
            "correct_reviews": sum(bool(r.correct) for r in reviews),
            "recurring_errors": await self.recurring_errors(user_id),
            "issue_trends": trends,
            "most_practiced_topics": [
                {"topic": topic, "count": count} for topic, count in topics.most_common(8)
            ],
            "source_counts": dict(Counter(i.source_skill for i in items)),
        }

    async def reuse(self, request, user_id):
        context = await self.source_context(request, user_id)
        if context["exam_mode"] == "FULL_TEST":
            return {"items": []}
        items = await self.db.scalars(
            select(UserVocabularyItem)
            .where(
                UserVocabularyItem.user_id == user_id,
                UserVocabularyItem.source_topic == context["topic"],
                UserVocabularyItem.mastery_level != "NEW",
                UserVocabularyItem.source_attempt_id != request.source_attempt_id,
            )
            .order_by(UserVocabularyItem.last_reviewed_at.desc())
            .limit(3)
        )
        return {
            "items": [
                {
                    "id": i.id,
                    "phrase": i.phrase,
                    "challenge_vi": f"Bạn có thể dùng ‘{i.phrase}’ tự nhiên trong một câu mới liên quan tới bài vừa luyện không?",
                }
                for i in items
            ]
        }

    async def create_review(self, item_id, data, user_id):
        await speech_lock(self.db, f"vocabulary-review-create:{user_id}:{data.client_request_id}")
        existing = await self.db.scalar(
            select(VocabularyReview).where(
                VocabularyReview.user_id == user_id,
                VocabularyReview.client_request_id == data.client_request_id,
            )
        )
        if existing:
            if existing.item_id != item_id or existing.kind != data.kind:
                raise AppError(409, "Yêu cầu đã dùng cho bài ôn khác.")
            await self.db.commit()
            return review_view(existing)
        item = await self.owned_item(item_id, user_id)
        expected = {"answers": item.exercise_data["accepted_phrases"]}
        prompt = {
            "instruction_vi": "Nhớ lại cụm từ tiếng Anh đã học.",
            "context": item.meaning_in_context_vi,
            "text": item.meaning_vi,
            "options": [],
        }
        if data.kind == "GAP":
            prompt.update(
                instruction_vi="Điền cụm từ đã học vào chỗ trống.",
                text=re.sub(re.escape(item.phrase), "_____", item.example_sentence, count=1, flags=re.I),
            )
            expected = {"answers": [item.phrase]}
        elif data.kind == "COLLOCATION":
            import random

            choices = [item.phrase, *item.exercise_data["collocation_distractors"]]
            random.shuffle(choices)
            prompt.update(
                instruction_vi="Chọn cụm từ tự nhiên để hoàn thành câu.",
                text=re.sub(re.escape(item.phrase), "_____", item.example_sentence, count=1, flags=re.I),
                options=choices,
            )
            expected = {"answers": [item.phrase]}
        elif data.kind == "CORRECT":
            if not item.user_original_text or not item.improved_text:
                raise AppError(422, "Mục này không có lỗi gốc để chữa. Chọn một dạng ôn khác.")
            prompt.update(
                instruction_vi="Sửa cách dùng từ trong câu/cụm từ cũ của bạn.", text=item.user_original_text
            )
            expected = {"answers": [item.improved_text, *item.exercise_data.get("natural_options", [])]}
        elif data.kind == "USE":
            prompt.update(
                instruction_vi="Viết một câu mới dùng cụm từ này tự nhiên trong ngữ cảnh đã học.",
                text=item.phrase,
            )
        review = VocabularyReview(
            user_id=user_id,
            item_id=item.id,
            kind=data.kind,
            prompt=prompt,
            expected=expected,
            client_request_id=data.client_request_id,
        )
        self.db.add(review)
        await self.db.commit()
        return review_view(review)

    async def owned_review(self, review_id, user_id, lock=False):
        query = select(VocabularyReview).where(
            VocabularyReview.id == review_id, VocabularyReview.user_id == user_id
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        review = await self.db.scalar(query)
        if not review:
            raise AppError(404, "Không tìm thấy lượt ôn.")
        return review

    async def answer_review(self, review_id, data, user_id):
        review = await self.owned_review(review_id, user_id, lock=True)
        if review.assessed_at:
            if review.answer != data.answer:
                raise AppError(409, "Lượt ôn này đã được chấm. Hãy mở lượt mới.")
            await self.db.commit()
            return review_view(review)
        item = await self.owned_item(review.item_id, user_id, lock=True)
        answer = data.answer.strip()
        if not answer:
            raise AppError(422, "Nhập câu trả lời trước khi gửi.")
        correct = normalized(answer) in {normalized(a) for a in review.expected["answers"]}
        confidence, model = 1.0, None
        explanation = (
            "Bạn đã nhớ đúng cách diễn đạt đang luyện."
            if correct
            else "Câu trả lời chưa khớp cách diễn đạt đang ôn. Đối chiếu cụm từ mẫu và thử lại ở lượt mới."
        )
        correction = item.improved_text if review.kind == "CORRECT" else item.phrase
        if review.kind == "USE":
            result = await self.llm.assess_vocabulary_usage(
                {
                    "phrase": item.phrase,
                    "meaning_vi": item.meaning_vi,
                    "meaning_in_context_vi": item.meaning_in_context_vi,
                    "patterns": item.common_patterns,
                    "sentence": answer,
                },
                user_id,
            )
            correct, confidence, model = (
                result.correct if result.confidence >= 0.8 else None,
                result.confidence,
                route_for("vocabulary_coach").model,
            )
            explanation, correction = result.explanation_vi, result.corrected_sentence
        now = utcnow()
        scheduled = item.next_review_at is None or item.next_review_at <= now
        item.review_count += 1
        item.correct_review_count += int(bool(correct))
        if correct is False:
            item.mastery_step = max(0, item.mastery_step - 1)
            item.mastery_level = "LEARNING"
            item.next_review_at = now + timedelta(days=1)
        elif correct and scheduled:
            days = [int(v) for v in settings.vocabulary_review_days.split(",")]
            item.mastery_step = min(item.mastery_step + 1, max(4, len(days)))
            item.mastery_level = (
                "MASTERED" if item.mastery_step >= 4 else "FAMILIAR" if item.mastery_step >= 2 else "LEARNING"
            )
            days = [int(v) for v in settings.vocabulary_review_days.split(",")]
            item.next_review_at = now + timedelta(days=days[min(item.mastery_step - 1, len(days) - 1)])
        item.last_reviewed_at = now
        review.answer, review.correct, review.assessed_at = data.answer, correct, now
        review.assessment_model, review.confidence = model, confidence
        review.feedback = {
            "explanation_vi": explanation,
            "suggested_answer": correction,
            "example_sentence": item.example_sentence,
            "mastery_level": item.mastery_level,
            "next_review_at": item.next_review_at.isoformat() if item.next_review_at else None,
            "progression_applied": correct is not None and (not correct or scheduled),
            "assessment": "AI practice feedback" if model else "Target-expression matching",
            "confidence": confidence,
        }
        await self.db.commit()
        try:
            from app.learning.vocabulary import sync_vocabulary_learning

            await sync_vocabulary_learning(user_id, review.id)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("Vocabulary learning update deferred")
        return review_view(review)
