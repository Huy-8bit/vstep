"""Opt-in live cost/cache/lazy-feedback walkthrough, using only a disposable account."""

import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from sqlalchemy import delete, select

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.llm.usage import ai_context
from app.main import app, hits
from app.models import AIUsageLog, User, WritingQuestion
from app.prompts.writing_calibration_anchors import ALEX_QUESTION, ALEX_RESPONSE


async def main(destination):
    identifier = None
    old_admin = settings.ai_cost_admin_emails
    report = {}
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=500
        ) as c:
            hits.clear()
            email = f"cost-check-{uuid4().hex}@example.com"
            r = await c.post("/api/v1/auth/register", json={"email": email, "password": uuid4().hex})
            assert r.status_code == 201, r.text
            identifier = r.json()["id"]
            assert (await c.get("/api/v1/internal/ai-costs")).status_code == 403
            settings.ai_cost_admin_emails = email
            async with SessionLocal() as db:
                q = WritingQuestion(
                    owner_id=identifier,
                    task_type=1,
                    question_type="informal_email",
                    topic="travel",
                    instruction=ALEX_QUESTION,
                    requirements=[
                        "Suggest time and travel",
                        "Recommend two places with reasons",
                        "Invite Alex",
                    ],
                    minimum_words=120,
                    source="USER",
                    fingerprint=hashlib.sha256(uuid4().bytes).hexdigest(),
                    genre="email",
                    register="informal",
                    recipient_relationship="friend",
                )
                db.add(q)
                await db.commit()
                qid = q.id
            attempts = []
            for i in range(2):
                r = await c.post(
                    "/api/v1/exams", json={"mode": "TASK1", "question_ids": [qid], "timed": False}
                )
                assert r.status_code == 201, r.text
                aid = r.json()["attempts"][0]["id"]
                attempts.append(aid)
                r = await c.post(
                    f"/api/v1/attempts/{aid}/submit", json={"answer": ALEX_RESPONSE, "revision": 0}
                )
                assert r.status_code == 200, r.text
                with ai_context(evaluation_id=str(uuid4())):
                    r = await c.post(f"/api/v1/attempts/{aid}/grade")
                assert r.status_code == 200, r.text
                g = r.json()["grading"]
                assert not g["corrected_version"] and not g["improved_b2_version"]
                report[f"attempt_{i}"] = {"scores": g["scores"], "model": g["ai_model"]}
                with ai_context(evaluation_id=str(uuid4())):
                    repeat = await c.post(f"/api/v1/attempts/{aid}/grade")
                assert repeat.json()["grading"]["id"] == g["id"]
            async with SessionLocal() as db:
                rows = list(await db.scalars(select(AIUsageLog).where(AIUsageLog.user_id == identifier)))
                assert rows and all(r.attempt_id == attempts[0] for r in rows), "Duplicate attempt paid again"
                assert all(r.operation in ("writing_core", "writing_escalation") for r in rows)
                report["core_calls"] = [
                    {"operation": r.operation, "model": r.model, "cost_usd": float(r.estimated_cost_usd or 0)}
                    for r in rows
                ]
            aid = attempts[0]
            before = g["scores"]
            with ai_context(evaluation_id=str(uuid4())):
                r = await c.post(f"/api/v1/attempts/{aid}/optional-feedback/corrected")
            assert r.status_code == 200, r.text
            assert r.json()["grading"]["corrected_version"] and not r.json()["grading"]["improved_b2_version"]
            assert r.json()["grading"]["scores"] == before
            with ai_context(evaluation_id=str(uuid4())):
                again = await c.post(f"/api/v1/attempts/{aid}/optional-feedback/corrected")
            assert again.status_code == 200, again.text
            async with SessionLocal() as db:
                rows = list(await db.scalars(select(AIUsageLog).where(AIUsageLog.user_id == identifier)))
                assert sum(r.operation == "writing_corrected" for r in rows) == 1
            r = await c.get(f"/api/v1/internal/ai-costs/attempts/{aid}")
            assert r.status_code == 200, r.text
            report["cost_ledger"] = r.json()
            overview = await c.get("/api/v1/internal/ai-costs")
            assert overview.status_code == 200, overview.text
            signals = await c.get(f"/api/v1/learning/attempts/WRITING/{aid}")
            assert signals.status_code == 200, signals.text
            report["checks"] = [
                "core-only initial grading",
                "identical grade replay",
                "cross-attempt content cache",
                "lazy corrected answer",
                "optional replay cache",
                "scores unchanged",
                "admin authorization",
                "per-attempt ledger",
                "learning integration",
            ]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
            print(
                json.dumps(
                    {k: v for k, v in report.items() if k != "cost_ledger"}, ensure_ascii=False, indent=2
                ),
                flush=True,
            )
    finally:
        settings.ai_cost_admin_emails = old_admin
        if identifier:
            async with SessionLocal() as db:
                await db.execute(delete(User).where(User.id == identifier))
                await db.commit()
        await engine.dispose()
        print("Disposable account removed; metering retained as evaluation spend", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("app/evals/runs/routed-flow.json"))
    asyncio.run(main(parser.parse_args().output))
