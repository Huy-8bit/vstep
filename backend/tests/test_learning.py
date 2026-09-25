"""Focused evidence-loop checks; only disposable accounts and fixtures are created."""

from datetime import timedelta
from types import SimpleNamespace as NS
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import delete, func, select

from app.db.base import utcnow
from app.db.session import SessionLocal
from app.learning.aggregation import evidence_trend, mastery_state
from app.learning.extraction import reading_data, speaking_data
from app.learning.signals import LearningSignalService
from app.learning.taxonomy import normalize
from app.llm.openai_client import OpenAILLMClient
from app.main import app, hits
from app.models import User, WritingAttempt, WritingError, WritingGrading
from app.models.commerce import UserEntitlement
from app.models.learning import LearningSignal, UserLearningEvent
from app.schemas.learning import PersonalizedExercisesOutput, PersonalizedLessonOutput


@pytest.mark.parametrize(
    "original,corrected,concept",
    [
        ("in the internet", "on the internet", "INTERNET_EXPRESSION"),
        ("in internet", "on the internet", "INTERNET_EXPRESSION"),
        ("on internet", "on the internet", "INTERNET_EXPRESSION"),
        ("I am agree", "I agree", "AGREE_USAGE"),
        ("I am very agree", "I strongly agree", "AGREE_USAGE"),
        ("many advantage", "many advantages", "ADVANTAGE_COUNTABILITY"),
        ("people is", "people are", "SUBJECT_VERB_AGREEMENT"),
    ],
)
def test_normalization(original, corrected, concept):
    assert normalize("grammar", "usage", original, corrected)[2] == concept


def evidence(attempt, outcome="ERROR", day=0, text="example"):
    return NS(
        skill="WRITING",
        attempt_id=attempt,
        created_at=utcnow() + timedelta(days=day),
        outcome=outcome,
        details={},
        original_text=text,
        severity="minor",
    )


def test_trends_use_exposure_and_do_not_reward_shorter_essays():
    attempts, signals = [], []
    for i in range(10):
        # Same two errors per 100 words; raw errors halve solely because word counts halve.
        attempts.append(
            NS(
                skill="WRITING",
                attempt_id=str(i),
                occurred_at=utcnow() + timedelta(days=i),
                exposure=200 if i < 5 else 100,
            )
        )
        signals.extend(evidence(str(i)) for _ in range(4 if i < 5 else 2))
    result = evidence_trend(signals, attempts, "GRAMMAR", "CROSS")
    assert result["trend"] == "STABLE" and result["older_rate"] == result["recent_rate"] == 2
    assert evidence_trend(signals, attempts[:3], "GRAMMAR", "CROSS")["trend"] == "INSUFFICIENT_DATA"


def test_mastery_needs_multiple_days_sessions_and_distinct_reuses_then_regresses():
    error = evidence("old", day=-20)
    one = NS(event_type="EXERCISE_CORRECT", source_exercise_id="session1", created_at=utcnow())
    assert mastery_state([error], [error], [one], "INSUFFICIENT_DATA", "NEW")[0] != "MASTERED"
    events = [
        NS(
            event_type="EXERCISE_CORRECT",
            source_exercise_id=f"session{i // 8}",
            created_at=utcnow() + timedelta(days=-5 + i // 8),
        )
        for i in range(24)
    ]
    same = [evidence(f"reuse{i}", "SUCCESS", day=-2, text="same memorized sentence") for i in range(3)]
    assert mastery_state([error], [error, *same], events, "IMPROVING", "LEARNING")[0] != "MASTERED"
    reuse = [evidence(f"reuse{i}", "SUCCESS", day=-2, text=f"new context {i}") for i in range(3)]
    assert mastery_state([error], [error, *reuse], events, "IMPROVING", "LEARNING")[0] == "MASTERED"
    events.append(NS(event_type="CONCEPT_MASTERED", created_at=utcnow() - timedelta(days=1)))
    new = [evidence("new1"), evidence("new2")]
    assert mastery_state([error, *new], [error, *reuse, *new], events, "STABLE", "MASTERED")[0] == "REGRESSED"
    after = [evidence(f"after{i}", "SUCCESS", day=1, text=f"new transfer {i}") for i in range(3)]
    assert (
        mastery_state([error, *new], [error, *reuse, *new, *after], events, "IMPROVING", "REGRESSED")[0]
        == "MASTERED"
    )


def test_reading_excludes_untrusted_keys_and_keeps_success_denominator():
    def answer(key, source, selected):
        return NS(
            question_id=str(uuid4()),
            selected_answer=selected,
            question=NS(
                id=str(uuid4()),
                correct_answer=key,
                answer_key_source=source,
                question_type="inference",
                question_text="What can be inferred?",
                option_explanations={"B": {"explanation_vi": "Option B exceeds the stated evidence."}},
                evidence=None,
            ),
        )

    session = NS(
        id=str(uuid4()),
        answers=[
            answer("A", "provided", "A"),
            answer("A", "provided", "B"),
            answer("A", "ai_suggested", "B"),
            answer(None, "unknown", "B"),
        ],
        result=NS(score=None),
        submitted_at=utcnow(),
    )
    result = reading_data(session)
    assert result["exposure"] == 2
    assert [s["outcome"] for s in result["signals"]] == ["SUCCESS", "ERROR"]
    assert result["signals"][1]["details"]["explanation_vi"] == "Option B exceeds the stated evidence."


def test_speaking_audio_provenance_and_sequence_dedup():
    transcript_error = NS(
        category="pronunciation",
        sequence_number=0,
        subtype="word_stress",
        original="online",
        corrected="",
        severity="minor",
        confidence=0.95,
        explanation_vi="Never use transcript as sound evidence",
    )
    grade = NS(
        cache_key="version",
        prompt_version="3",
        created_at=utcnow(),
        ai_model="fixture",
        errors=[transcript_error],
        answer_feedback=[],
        grammar_score=6,
        vocabulary_score=6,
        pronunciation_score=None,
        fluency_score=None,
        structures_score=6,
        overall_score=None,
    )
    a = NS(
        id="a",
        sequence_number=0,
        part=3,
        transcript="I found the information online.",
        audio_hash="real-hash",
        audio_analysis={"available": False},
        grading=None,
    )
    session = NS(id="s", answers=[a], grading=grade, completed_at=utcnow())
    assert not speaking_data(session)["signals"]
    issue = {
        "type": "hesitation",
        "target": "before reasons",
        "description_vi": "Khoảng dừng dài trước phần lý do.",
        "suggestion_vi": "Chia ý thành cụm ngắn.",
        "confidence": 0.9,
        "audible_evidence_vi": "Âm thanh có khoảng dừng dài sau câu đầu.",
    }
    a.audio_analysis = {"available": True, "speech_present": True, "issues": [issue]}
    rows = speaking_data(session)["signals"]
    assert rows[0]["concept_key"] == "LONG_PAUSES" and rows[0]["details"]["evidence_kind"] == "audio"
    issue["confidence"] = 0.3
    assert not speaking_data(session)["signals"]


@pytest_asyncio.fixture
async def accounts():
    ids = []
    hits.clear()
    async with (
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as first,
        httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as other,
    ):
        for c in (first, other):
            r = await c.post(
                "/api/v1/auth/register",
                json={"email": f"learning-{uuid4().hex}@example.com", "password": "ExamplePassword123!"},
            )
            assert r.status_code == 201, r.text
            ids.append(r.json()["id"])
        async with SessionLocal() as db:
            db.add_all(UserEntitlement(user_id=uid, source="ADMIN_GRANT", entitlement_type="VIP", starts_at=utcnow(), expires_at=utcnow() + timedelta(days=30), status="ACTIVE", details={"reason": "legacy integration fixture"}) for uid in ids)
            await db.commit()
        yield first, other, ids
    async with SessionLocal() as db:
        await db.execute(delete(User).where(User.id.in_(ids)))
        await db.commit()


async def graded_fixture(client, user_id, original="in internet", day=0):
    created = await client.post("/api/v1/exams", json={"mode": "TASK2", "timed": False})
    assert created.status_code == 201, created.text
    aid = created.json()["attempts"][0]["id"]
    async with SessionLocal() as db:
        attempt = await db.get(WritingAttempt, aid)
        attempt.answer = f"People find useful information {original}."
        attempt.word_count = len(attempt.answer.split())
        attempt.status = "GRADED"
        attempt.submitted_at = utcnow() + timedelta(days=day)
        attempt.grading = WritingGrading(
            attempt_id=aid,
            cache_key=uuid4().hex,
            task_fulfillment_score=6,
            organization_score=6,
            vocabulary_score=6,
            grammar_score=5,
            overall_score=5.75,
            summary_vi="Fixture assessment",
            strengths=[],
            priority_improvements=[],
            structure_feedback=[],
            task_fulfillment_feedback=[],
            vocabulary_suggestions=[],
            sentence_feedback=[],
            corrected_version=attempt.answer.replace(original, "on the internet"),
            improved_b2_version="",
            ai_model="fixture",
            prompt_version="test",
            grader_version="test-v1",
            analysis_snapshot={},
            criterion_evidence={},
        )
        attempt.grading.errors = [
            WritingError(
                category="grammar",
                subtype="preposition",
                original_text=original,
                corrected_text="on the internet",
                explanation_vi="Dùng on the internet.",
                severity="minor",
            )
        ]
        await db.commit()
        await LearningSignalService(db).extract(user_id, "WRITING", aid)
        await db.commit()
    return aid


async def test_versioned_extraction_backfill_privacy_and_plans(accounts):
    client, other, ids = accounts
    aids = []
    for i, original in enumerate(("in internet", "in the internet", "on internet")):
        aids.append(await graded_fixture(client, ids[0], original, day=i - 5))
    response = await client.get("/api/v1/learning/weaknesses")
    assert response.status_code == 200, response.text
    w = response.json()["items"][0]
    assert (
        w["concept_key"] == "INTERNET_EXPRESSION"
        and w["occurrence_count"] == 3
        and w["status"] == "RECURRING"
    )
    async with SessionLocal() as db:
        assert not await LearningSignalService(db).extract(ids[0], "WRITING", aids[0])
        a = await db.get(WritingAttempt, aids[0])
        a.grading.grader_version = "test-v2"
        await db.commit()
        assert await LearningSignalService(db).extract(ids[0], "WRITING", aids[0])
        await db.commit()
        assert (
            await db.scalar(
                select(func.count()).select_from(LearningSignal).where(LearningSignal.user_id == ids[0])
            )
            == 4
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(LearningSignal)
                .where(LearningSignal.user_id == ids[0], LearningSignal.active.is_(True))
            )
            == 3
        )
    assert (await other.get(f"/api/v1/learning/weaknesses/{w['id']}")).status_code == 404
    assert (await other.post(f"/api/v1/learning/weaknesses/{w['id']}/lesson")).status_code == 404
    assert (await other.get(f"/api/v1/learning/attempts/WRITING/{aids[0]}")).status_code == 404
    assert (await client.get("/api/v1/learning/overview")).status_code == 200
    assert (await client.get("/api/v1/learning/overview")).json()["backfill_status"] == "COMPLETE"
    plan = await client.post("/api/v1/learning/study-plan", json={"duration_days": 14, "daily_minutes": 25})
    assert plan.status_code == 201, plan.text
    assert len(plan.json()["items"]) == 28
    item = plan.json()["items"][0]
    assert (
        await other.patch(f"/api/v1/learning/study-plan/items/{item['id']}", json={"status": "COMPLETED"})
    ).status_code == 404
    assert (
        await client.patch(f"/api/v1/learning/study-plan/items/{item['id']}", json={"status": "COMPLETED"})
    ).status_code == 200
    assert (await client.get(f"/api/v1/learning/weaknesses/{w['id']}")).json()["status"] != "MASTERED"
    assert (await client.get("/api/v1/learning/today")).json()["estimated_minutes"] <= 25


async def test_lesson_and_exercise_loop_hides_keys_and_prevents_replay(accounts, monkeypatch):
    client, other, ids = accounts
    await graded_fixture(client, ids[0])
    w = (await client.get("/api/v1/learning/weaknesses")).json()["items"][0]
    calls = []

    async def structured(self, schema, prompt, payload, user_id, operation, validate=None, **kwargs):
        calls.append(operation)
        if schema is PersonalizedLessonOutput:
            e = payload["evidence"][0]
            result = schema(
                title="On the internet",
                why_this_matters_vi="Dùng đúng giới từ và mạo từ.",
                simple_explanation_vi="Dùng on the internet khi nói về thông tin trực tuyến.",
                rules=["Dùng on trước the internet."],
                examples=[
                    {"english": "I read news on the internet.", "explanation_vi": "Thông tin trực tuyến."},
                    {"english": "We shop on the internet.", "explanation_vi": "Mua sắm trực tuyến."},
                ],
                examples_from_user_errors=[
                    {
                        "signal_id": e["signal_id"],
                        "original": e["original"],
                        "corrected": e["corrected"],
                        "explanation_vi": "Dùng cụm on the internet.",
                    }
                ],
                common_traps=["Không dùng in internet."],
                quick_check=["Giới từ nào đứng trước the internet?"],
                practice_recommendation="Luyện 5 câu mới.",
            )
        elif schema is PersonalizedExercisesOutput:
            result = schema(
                title="Cụm từ trong ngữ cảnh",
                concept_key=payload["concept_key"],
                items=[
                    {
                        "kind": "MULTIPLE_CHOICE",
                        "instruction_vi": "Chọn cụm từ phù hợp.",
                        "text": f"Context {i}: We found it _____.",
                        "options": ["on the internet", "in internet", "at internet"],
                        "accepted_answers": ["on the internet"],
                        "sample_answer": "on the internet",
                        "explanation_vi": "Dùng on the internet trong ngữ cảnh này.",
                        "rubric": ["Đúng giới từ và mạo từ"],
                        "passage": None,
                        "target_words": [],
                        "seconds": None,
                        "evaluation": "OBJECTIVE",
                    }
                    for i in range(payload["count"])
                ],
            )
        else:
            raise AssertionError(operation)
        if validate:
            validate(result)
        return result

    monkeypatch.setattr(OpenAILLMClient, "_structured", structured)
    path = f"/api/v1/learning/weaknesses/{w['id']}"
    lesson = await client.post(path + "/lesson")
    assert lesson.status_code == 200, lesson.text
    assert (await client.post(path + "/lesson")).json()["id"] == lesson.json()["id"]
    assert calls.count("learning_lesson") == 1
    req = {"client_request_id": str(uuid4()), "count": 5, "kind": "MULTIPLE_CHOICE"}
    created = await client.post(path + "/practice", json=req)
    assert created.status_code == 201, created.text
    ex = created.json()
    assert "accepted_answers" not in ex["items"][0] and "sample_answer" not in ex["items"][0]
    assert (await client.post(path + "/practice", json=req)).json()["id"] == ex["id"]
    assert calls.count("learning_exercises") == 1
    ep = f"/api/v1/learning/exercises/{ex['id']}"
    assert (await other.get(ep)).status_code == 404
    answer = {"item_index": 0, "answer": "on the internet", "duration_seconds": 20}
    assert (await other.post(ep + "/answer", json=answer)).status_code == 404
    graded = await client.post(ep + "/answer", json=answer)
    assert graded.status_code == 200, graded.text
    assert graded.json()["items"][0]["result"]["correct"] is True
    assert (await client.post(ep + "/answer", json=answer)).status_code == 200
    assert (await client.post(ep + "/answer", json={**answer, "answer": "in internet"})).status_code == 409
    assert (await client.get(path)).json()["status"] != "MASTERED"
    async with SessionLocal() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(UserLearningEvent)
                .where(
                    UserLearningEvent.user_id == ids[0], UserLearningEvent.event_type == "EXERCISE_CORRECT"
                )
            )
            == 1
        )
    for index in range(1, 5):
        r = await client.post(ep + "/answer", json={**answer, "item_index": index})
        assert r.status_code == 200, r.text
    assert r.json()["completed_at"] is not None


async def test_weekly_ai_uses_aggregates_private_cache_and_new_evidence_invalidates(accounts, monkeypatch):
    from app.schemas.learning import WeeklyCoachOutput

    client, other, ids = accounts
    await graded_fixture(client, ids[0])
    await client.get("/api/v1/learning/overview")
    calls = []

    async def structured(self, schema, prompt, payload, user_id, operation, validate=None, **kwargs):
        assert schema is WeeklyCoachOutput and operation == "learning_weekly_summary"
        assert "original_text" not in str(payload) and "People find useful information" not in str(payload)
        calls.append(payload)
        priority = payload["priorities"][0]
        result = schema(
            summary_vi="Đã ghi nhận lỗi dùng cụm từ. Cần thêm bài làm để xác định xu hướng.",
            recommendations=[
                {
                    "weakness_id": priority["weakness_id"],
                    "reason_vi": "Cụm từ đã xuất hiện trong bài đã chấm.",
                    "activity_vi": "Học cách dùng cụm từ rồi viết câu mới trong ngữ cảnh khác.",
                }
            ],
        )
        invalid = result.model_copy(deep=True)
        invalid.recommendations[0].weakness_id = "another-users-weakness"
        with pytest.raises(ValueError):
            validate(invalid)
        validate(result)
        return result

    monkeypatch.setattr(OpenAILLMClient, "_structured", structured)
    generated = await client.post("/api/v1/learning/weekly/summary")
    assert generated.status_code == 200, generated.text
    assert (await client.post("/api/v1/learning/weekly/summary")).json() == generated.json()
    assert len(calls) == 1
    assert (await client.get("/api/v1/learning/weekly")).json()["ai_summary"] == generated.json()
    assert (await other.get("/api/v1/learning/weekly")).json()["ai_summary"] is None
    await graded_fixture(client, ids[0], original="on internet")
    assert (await client.get("/api/v1/learning/weekly")).json()["ai_summary"] is None
    assert (await client.post("/api/v1/learning/weekly/summary")).status_code == 200
    assert len(calls) == 2


async def test_retake_archives_old_signals_without_counting_ungraded_audio(accounts):
    from app.models.learning import LearningAttempt
    from app.models.speaking import SpeakingExamSession

    _, _, ids = accounts
    async with SessionLocal() as db:
        session = SpeakingExamSession(user_id=ids[0], mode="PART3", question_set=[], grading=None, answers=[])
        db.add(session)
        await db.flush()
        db.add(
            LearningAttempt(
                user_id=ids[0],
                skill="SPEAKING",
                attempt_id=session.id,
                source_version="old",
                analysis_version="1",
                occurred_at=utcnow(),
                exposure=100,
                scores={"grammar": 5},
                lexical_counts={},
                source_url=f"/speaking/result/{session.id}",
            )
        )
        db.add(
            LearningSignal(
                user_id=ids[0],
                skill="SPEAKING",
                attempt_id=session.id,
                category="GRAMMAR",
                subcategory="AGREE_USAGE",
                concept_key="AGREE_USAGE",
                original_text="I am agree",
                corrected_text="I agree",
                severity="minor",
                confidence=0.9,
                outcome="ERROR",
                details={},
                fingerprint="old",
                source_version="old",
                grader_version="old",
                analysis_version="1",
                taxonomy_version="1",
            )
        )
        await db.commit()
        await LearningSignalService(db).extract(ids[0], "SPEAKING", session.id)
        await db.commit()
        assert not await db.scalar(select(LearningAttempt.id).where(LearningAttempt.user_id == ids[0]))
        archived = await db.scalar(select(LearningSignal).where(LearningSignal.user_id == ids[0]))
        assert archived and not archived.active


@pytest.mark.parametrize(
    "category,concept",
    [
        ("spelling", "SPELLING"),
        ("punctuation", "PUNCTUATION"),
        ("collocation", "COLLOCATION"),
        ("word_choice", "WORD_CHOICE"),
        ("cohesion", "WEAK_COHESION"),
        ("register", "REGISTER_MISMATCH"),
    ],
)
def test_writing_categories_keep_their_teachable_domain(category, concept):
    assert normalize(category, "usage", "original", "corrected", skill="WRITING")[2] == concept


def test_existing_correct_phrase_is_not_misdiagnosed_during_normalization():
    assert (
        normalize(
            "grammar",
            "subject_verb_agreement",
            "She are interested in history.",
            "She is interested in history.",
        )[2]
        == "SUBJECT_VERB_AGREEMENT"
    )
    assert (
        normalize(
            "grammar",
            "subject_verb_agreement",
            "He want to study on the internet.",
            "He wants to study on the internet.",
        )[2]
        == "SUBJECT_VERB_AGREEMENT"
    )


async def test_targeted_reading_bank_uses_ten_trusted_questions_and_existing_engine(accounts):
    client, other, _ = accounts
    created = await client.post(
        "/api/v1/reading/sessions",
        json={"mode": "QUESTION_TYPE_PRACTICE", "target_question_type": "inference", "timed": False},
    )
    assert created.status_code == 201, created.text
    submitted = await client.post(
        f"/api/v1/reading/sessions/{created.json()['id']}/submit", json={"answers": {}}
    )
    assert submitted.status_code == 200, submitted.text
    w = (await client.get("/api/v1/learning/weaknesses?skill=READING")).json()["items"][0]
    request = {"client_request_id": str(uuid4()), "skill": "READING", "source": "BANK"}
    started = await client.post(f"/api/v1/learning/weaknesses/{w['id']}/targeted-practice", json=request)
    assert started.status_code == 201, started.text
    result = started.json()
    retried = await client.post(f"/api/v1/learning/weaknesses/{w['id']}/targeted-practice", json=request)
    assert retried.json()["attempt_id"] == result["attempt_id"]
    session = await client.get(f"/api/v1/reading/sessions/{result['attempt_id']}")
    assert session.json()["question_count"] == 10 and session.json()["mode"] == "QUESTION_TYPE_PRACTICE"
    assert (await other.get(f"/api/v1/reading/sessions/{result['attempt_id']}")).status_code == 404
