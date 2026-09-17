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
        result = {
            "task": payload["task"],
            "word_count": 999,
            "scores": {"task_fulfillment": 7, "organization": 6, "vocabulary": 6, "grammar": 5, "overall": 9},
            "summary_vi": "Bài cần phát triển thêm.",
            "strengths": ["Có quan điểm rõ."],
            "priority_improvements": [improvement] * 3,
            "structure_feedback": [improvement],
            "task_fulfillment_feedback": [improvement],
            "errors": [
                {
                    "category": "grammar",
                    "subtype": "verb_tense",
                    "original": "I have went",
                    "corrected": "I went",
                    "explanation_vi": "Dùng thì quá khứ đơn.",
                    "severity": "major",
                }
            ],
            "vocabulary_suggestions": [],
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
    assert len(calls) == 2
    assert results[0].json()["grading"]["scores"]["overall"] == 6
    assert results[0].json()["word_count"] == 5
    assert (await client.post(f"/api/v1/attempts/{b['id']}/grade")).status_code == 200
    assert len(calls) == 3
    assert (await client.get(f"/api/v1/exams/{e['id']}")).json()["overall_score"] == 6
    duplicate = await client.post(
        "/api/v1/exams", json={"mode": "TASK1", "question_ids": [a["question"]["id"]]}
    )
    dup = duplicate.json()["attempts"][0]
    await client.post(
        f"/api/v1/attempts/{dup['id']}/submit", json={"answer": "I have went there yesterday.", "revision": 0}
    )
    assert (await client.post(f"/api/v1/attempts/{dup['id']}/grade")).status_code == 200
    assert len(calls) == 3  # Same question+answer+model+prompt cached across attempts.
    summary = (await client.get("/api/v1/progress/summary")).json()
    assert summary["graded_attempts"] == 3 and summary["average_writing_score"] == 6
    errors = (await client.get("/api/v1/progress/errors")).json()
    assert errors[0]["count"] == 3
    async with SessionLocal() as db:
        assert (
            await db.scalar(
                select(func.count()).select_from(AIUsageLog).where(AIUsageLog.user_id == client.test_user_id)
            )
            == 3
        )


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
    assert r.json()["minimum_words"] == 120 and len(r.json()["requirements"]) == 3
    assert (
        await client.post("/api/v1/questions/generate", json={"task": 1, "question_type": "opinion"})
    ).status_code == 422
