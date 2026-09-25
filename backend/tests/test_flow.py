"""Small PostgreSQL integration checks; only disposable test users are removed."""

import asyncio
import json
from datetime import timedelta
from uuid import uuid4

import httpx
import pytest_asyncio
from openai import AsyncOpenAI
from sqlalchemy import delete, func, select

from app.core.config import settings
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.llm import openai_client
from app.main import app, hits
from app.models import AIUsageLog, ExamSession, User, WritingQuestion
from app.models.commerce import UserEntitlement


@pytest_asyncio.fixture
async def client():
    hits.clear()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": settings.frontend_url},
    ) as c:
        credentials = {"email": f"integration-{uuid4().hex}@example.com", "password": "ExamplePassword123!"}
        response = await c.post("/api/v1/auth/register", json=credentials)
        assert response.status_code == 201, response.text
        c.test_user_id = response.json()["id"]
        c.test_credentials = credentials
        async with SessionLocal() as db:
            db.add(UserEntitlement(user_id=c.test_user_id, source="ADMIN_GRANT", entitlement_type="VIP", starts_at=utcnow(), expires_at=utcnow() + timedelta(days=30), status="ACTIVE", details={"reason": "legacy integration fixture"}))
            await db.commit()
        yield c
    async with SessionLocal() as db:
        await db.execute(delete(User).where(User.id == c.test_user_id))
        await db.commit()


async def exam(client, mode="FULL_TEST"):
    r = await client.post("/api/v1/exams", json={"mode": mode})
    assert r.status_code == 201, r.text
    return r.json()


async def test_auth_rotation_logout_and_ownership(client):
    previous = client.cookies.get("vstep_refresh")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 200
    assert previous != client.cookies.get("vstep_refresh")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test", cookies={"vstep_refresh": previous}
    ) as replay:
        assert (await replay.post("/api/v1/auth/refresh")).status_code == 401
    e = await exam(client)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as other:
        assert (await other.get(f"/api/v1/exams/{e['id']}")).status_code == 401
        second = await other.post(
            "/api/v1/auth/register",
            json={"email": f"integration-{uuid4().hex}@example.com", "password": "ExamplePassword123!"},
        )
        second_id = second.json()["id"]
        try:
            assert (await other.get(f"/api/v1/exams/{e['id']}")).status_code == 404
            assert (
                await other.patch(
                    f"/api/v1/attempts/{e['attempts'][0]['id']}", json={"answer": "overwrite", "revision": 0}
                )
            ).status_code == 404
            assert (await other.get("/api/v1/attempts")).json()["total"] == 0
        finally:
            async with SessionLocal() as db:
                await db.execute(delete(User).where(User.id == second_id))
                await db.commit()
    assert (await client.post("/api/v1/auth/logout")).status_code == 200
    assert (await client.get("/api/v1/auth/me")).status_code == 401
    assert (await client.post("/api/v1/auth/login", json=client.test_credentials)).status_code == 200
    assert (
        await client.post(
            "/api/v1/exams", json={"mode": "TASK1"}, headers={"Origin": "https://untrusted.example"}
        )
    ).status_code == 403


async def test_autosave_full_submission_and_no_key(client, monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    e = await exam(client)
    a, b = e["attempts"]
    path = f"/api/v1/attempts/{a['id']}"
    assert (await client.post(f"{path}/grade")).status_code == 409
    update = {"answer": "Dear Alex, I am happy to hear from you.", "revision": 0}
    saved = await client.patch(path, json=update)
    assert saved.status_code == 200
    assert saved.json()["word_count"] == 9
    assert (await client.patch(path, json=update)).status_code == 200  # lost acknowledgement
    assert (await client.patch(path, json={"answer": "stale change", "revision": 0})).status_code == 409
    reloaded = (await client.get(f"/api/v1/exams/{e['id']}")).json()
    assert reloaded["expires_at"] == e["expires_at"]
    assert reloaded["attempts"][0]["answer"] == update["answer"]
    assert (await client.post(f"{path}/submit", json=update)).status_code == 409
    submitted = await client.post(
        f"/api/v1/exams/{e['id']}/submit",
        json={"answers": {b["id"]: {"answer": "Education is essential for everyone.", "revision": 0}}},
    )
    assert submitted.status_code == 200, submitted.text
    assert all(a["status"] == "SUBMITTED" for a in submitted.json()["attempts"])
    assert (await client.patch(path, json=update)).status_code == 409
    grading = await client.post(f"{path}/grade")
    assert grading.status_code == 503 and grading.json()["code"] == "ai_not_configured"
    assert (await client.get("/api/v1/attempts?mode=FULL_TEST")).json()["total"] == 2


async def test_expiry_rejects_late_writes(client):
    e = await exam(client, "TASK1")
    async with SessionLocal() as db:
        session = await db.get(ExamSession, e["id"])
        session.expires_at = utcnow() - timedelta(seconds=1)
        await db.commit()
    r = await client.patch(
        f"/api/v1/attempts/{e['attempts'][0]['id']}", json={"answer": "too late", "revision": 0}
    )
    assert r.status_code == 409 and r.json()["code"] == "exam_closed"
    expired = (await client.get(f"/api/v1/exams/{e['id']}")).json()
    assert expired["status"] == "EXPIRED" and expired["attempts"][0]["answer"] == ""


async def test_real_sdk_structured_retry_cache_and_progress(client, monkeypatch):
    """Use the real SDK/parse path against a deterministic HTTP transport, never a production mock provider."""
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    calls = []

    def respond(request):
        body = json.loads(request.content)
        payload = json.loads(body["input"][1]["content"])
        calls.append(body)
        assert body["text"]["format"]["type"] == "json_schema"
        improvement = {
            "title_vi": "Phát triển ý",
            "explanation_vi": "Thêm ví dụ cụ thể.",
            "example": "For example, students can practise daily.",
        }
        # The SDK fixture follows the current evidence -> calibration -> feedback pipeline.
        schema = body["text"]["format"]["name"]
        evidence = {
            "positive_evidence": [],
            "negative_evidence": [],
            "assessment_vi": "Bằng chứng giới hạn trong bài thử.",
        }
        criteria = ("task_fulfillment", "organization", "vocabulary", "grammar")
        if schema == "WritingAnalysis":
            result = {
                "task": payload["task"],
                "task_coverage": [
                    {"requirement": requirement, "coverage": "missing", "evidence": []}
                    for requirement in (payload["requirements"] or [payload["instruction"]])
                ],
                "idea_development": "basic",
                "cohesion": "basic",
                "lexical_range": "basic",
                "criteria": {key: evidence for key in criteria},
                "sentences": [
                    {
                        "sentence_id": sentence["sentence_id"],
                        "structure": "simple",
                        "relative_clauses": 0,
                        "conditionals": 0,
                        "subordination": 0,
                        "control": "partly_controlled",
                    }
                    for sentence in payload["sentences"]
                ],
                "errors": [
                    {
                        "sentence_id": 1,
                        "primary_criterion": "grammar",
                        "category": "grammar",
                        "subtype": "verb_tense",
                        "original": "I have went",
                        "corrected": "I went",
                        "explanation_vi": "Dùng thì quá khứ đơn.",
                        "severity": "major",
                    }
                ],
                "relevance_vi": "Bài thử rất ngắn.",
                "register_vi": "Chưa đủ bằng chứng về văn phong.",
            }
        elif schema == "WritingCalibration":
            result = {
                key: {
                    **evidence,
                    "initial_score": 6,
                    "score": 6,
                    "score_justification_vi": "Điểm cố định chỉ để kiểm tra luồng dữ liệu trong test SDK.",
                    "consistency_review_vi": "Bằng chứng được giữ nguyên qua bước hiệu chỉnh điểm trong test.",
                    "high_score_justification_vi": "",
                }
                for key in criteria
            }
            result["calibration_summary_vi"] = "Kết quả xác định để kiểm tra SDK, không phải chấm bài thật."
        elif schema == "WritingFeedback":
            result = {
                "summary_vi": "Bài cần phát triển thêm.",
                "strengths": ["Có một ý ngắn."],
                "priority_improvements": [improvement] * 3,
                "structure_feedback": [improvement],
                "task_fulfillment_feedback": [improvement],
                "vocabulary_suggestions": [],
            }
        elif schema == "WritingCorrections":
            result = {
                "sentence_feedback": [
                    {
                        "original": payload["user_answer"],
                        "corrected": "I went there yesterday.",
                        "explanation_vi": "Dùng thì quá khứ đơn.",
                    }
                ],
                "corrected_version": "I went there yesterday.",
                "improved_b2_version": "I visited the place yesterday.",
            }
        elif schema == "VocabularyCoachOutput":
            result = {
                "items": [
                    {
                        "headword": phrase,
                        "phrase": phrase,
                        "part_of_speech": "noun phrase",
                        "meaning_vi": "Cụm từ hữu ích trong học tập",
                        "meaning_in_context_vi": "Dùng khi mô tả việc học ngôn ngữ",
                        "register": "neutral",
                        "collocations": [phrase],
                        "common_patterns": [phrase],
                        "user_original": "",
                        "better_version": "",
                        "example_sentence": f"Students benefit from {phrase}.",
                        "why_learn_this_vi": "Cụm từ dùng được khi thảo luận chủ đề giáo dục.",
                        "source_type": "TOPIC",
                        "issue_type": "lexical_gap",
                        "priority": "MEDIUM",
                        "natural_options": [phrase],
                        "collocation_distractors": ["option one", "option two", "option three"],
                        "accepted_phrases": [phrase],
                    }
                    for phrase in (
                        "daily practice",
                        "regular feedback",
                        "language skills",
                        "study habits",
                        "clear goals",
                    )
                ]
            }
        else:
            raise AssertionError(f"Unhandled current SDK schema: {schema}")
        # First response is invalid; the adapter must retry once, not crash or use regex.
        output = "{}" if len(calls) == 1 else json.dumps(result, ensure_ascii=False)
        return httpx.Response(
            200,
            json={
                "id": f"resp_{len(calls)}",
                "object": "response",
                "created_at": 1,
                "status": "completed",
                "model": settings.openai_model,
                "output": [
                    {
                        "type": "message",
                        "id": "msg_test",
                        "role": "assistant",
                        "status": "completed",
                        "content": [{"type": "output_text", "text": output, "annotations": []}],
                    }
                ],
                "usage": {"input_tokens": 100, "output_tokens": 300, "total_tokens": 400},
            },
        )

    monkeypatch.setattr(
        openai_client,
        "AsyncOpenAI",
        lambda **kwargs: AsyncOpenAI(
            **kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond))
        ),
    )
    e = await exam(client)
    await client.post(
        f"/api/v1/exams/{e['id']}/submit",
        json={
            "answers": {
                a["id"]: {"answer": "I have went there yesterday.", "revision": 0} for a in e["attempts"]
            }
        },
    )
    a, b = e["attempts"]
    # Concurrent identical requests must share one saved result.
    results = await asyncio.gather(*(client.post(f"/api/v1/attempts/{a['id']}/grade") for _ in range(2)))
    assert all(r.status_code == 200 for r in results), [r.text for r in results]
    assert len(calls) == 6
    assert results[0].json()["grading"]["scores"]["overall"] == 6
    assert results[0].json()["word_count"] == 5
    assert (await client.post(f"/api/v1/attempts/{b['id']}/grade")).status_code == 200
    assert len(calls) == 11
    assert (await client.get(f"/api/v1/exams/{e['id']}")).json()["overall_score"] == 6
    duplicate = await client.post(
        "/api/v1/exams", json={"mode": "TASK1", "question_ids": [a["question"]["id"]]}
    )
    dup = duplicate.json()["attempts"][0]
    await client.post(
        f"/api/v1/attempts/{dup['id']}/submit", json={"answer": "I have went there yesterday.", "revision": 0}
    )
    assert (await client.post(f"/api/v1/attempts/{dup['id']}/grade")).status_code == 200
    # Reusing a question+answer preserves evidence/calibration/correction; feedback and
    # vocabulary can be attached independently to the new attempt.
    schemas = [call["text"]["format"]["name"] for call in calls]
    assert schemas.count("WritingAnalysis") == 3  # Two tasks plus the one invalid response.
    assert schemas.count("WritingCalibration") == schemas.count("WritingCorrections") == 2
    summary = (await client.get("/api/v1/progress/summary")).json()
    assert summary["graded_attempts"] == 3 and summary["average_writing_score"] == 6
    errors = (await client.get("/api/v1/progress/errors")).json()
    assert errors[0]["count"] == 3
    async with SessionLocal() as db:
        assert await db.scalar(
            select(func.count()).select_from(AIUsageLog).where(AIUsageLog.user_id == client.test_user_id)
        ) == len(calls)


async def test_seed_format_and_filter(client):
    async with SessionLocal() as db:
        for task in (1, 2):
            assert (
                await db.scalar(
                    select(func.count())
                    .select_from(WritingQuestion)
                    .where(WritingQuestion.task_type == task, WritingQuestion.source == "SEED")
                )
                >= 10
            )
    r = await client.post(
        "/api/v1/questions/generate", json={"task": 1, "question_type": "formal_email", "source": "SEED"}
    )
    assert r.status_code == 200
    assert r.json()["minimum_words"] == 120 and r.json()["stimulus"] and r.json()["response_instruction"]
    assert r.json()["requirements"] == []  # Current generated Task 1 requirements are inside the stimulus.
    assert (
        await client.post("/api/v1/questions/generate", json={"task": 1, "question_type": "opinion"})
    ).status_code == 422
