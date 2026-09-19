"""Opt-in live AI check. Deletes only its own disposable account in finally."""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import httpx
from sqlalchemy import delete, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.session import SessionLocal, engine
from app.llm.openai_client import OpenAILLMClient
from app.main import app, hits
from app.models import User, WritingQuestion
from tests.test_learning import graded_fixture

if "--diagnostics" in sys.argv:
    original_review = OpenAILLMClient.review_question_quality

    async def diagnostic_review(self, payload, user_id):
        result = await original_review(self, payload, user_id)
        if payload.get("skill") == "READING":
            keys = {q["question_number"]: q["correct_answer"] for q in payload["material"]["questions"]}
            print(
                "Reading review:",
                {
                    "accepted": result.accepted,
                    "confidence": result.confidence,
                    "notes": result.notes,
                    "items": [
                        {
                            "number": i.question_number,
                            "confidence": i.confidence,
                            "single": i.single_best_answer,
                            "supported": i.supported_by_evidence,
                            "distractors": i.plausible_distractors,
                            "key_matches": i.independently_selected_answer == keys[i.question_number],
                        }
                        for i in result.reading_items
                    ],
                },
                flush=True,
            )
        return result

    OpenAILLMClient.review_question_quality = diagnostic_review


async def main():
    user_id = None
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test", timeout=240
        ) as client:
            hits.clear()
            registered = await client.post(
                "/api/v1/auth/register",
                json={"email": f"learning-live-{uuid4().hex}@example.com", "password": uuid4().hex},
            )
            assert registered.status_code == 201, registered.text
            user_id = registered.json()["id"]
            await graded_fixture(client, user_id)
            if "--weekly-only" in sys.argv:
                await client.get("/api/v1/learning/overview")
                review = await client.post("/api/v1/learning/weekly/summary")
                assert review.status_code == 200, review.text
                assert review.json()["recommendations"]
                assert (await client.post("/api/v1/learning/weekly/summary")).json() == review.json()
                print(
                    "live weekly summary: structured analytics, referenced actions, cached replay", flush=True
                )
                return
            w = (await client.get("/api/v1/learning/weaknesses")).json()["items"][0]
            path = f"/api/v1/learning/weaknesses/{w['id']}"
            if "--targeted-only" not in sys.argv:
                lesson = await client.post(path + "/lesson")
                assert lesson.status_code == 200, lesson.text
                print("live lesson: personalized sources validated", flush=True)
                exercise = await client.post(
                    path + "/practice",
                    json={"client_request_id": str(uuid4()), "kind": "MULTIPLE_CHOICE", "count": 5},
                )
                assert exercise.status_code == 201, exercise.text
                exercise = exercise.json()
                assert len(exercise["items"]) == 5 and all(
                    "accepted_answers" not in i for i in exercise["items"]
                )
                answered = await client.post(
                    f"/api/v1/learning/exercises/{exercise['id']}/answer",
                    json={
                        "item_index": 0,
                        "answer": exercise["items"][0]["options"][0],
                        "duration_seconds": 0,
                    },
                )
                assert answered.status_code == 200, answered.text
                print("live exercise: 5 generated; answer key hidden; feedback persisted", flush=True)
            if "--other-skills" not in sys.argv:
                targeted = await client.post(
                    path + "/targeted-practice",
                    json={"client_request_id": str(uuid4()), "skill": "WRITING", "part": 2},
                )
                assert targeted.status_code == 201, targeted.text
                async with SessionLocal() as db:
                    private = list(
                        await db.scalars(select(WritingQuestion).where(WritingQuestion.owner_id == user_id))
                    )
                    assert private and private[0].generation_diagnostics.get("learning_focus")
                print("live targeted Writing: private focused task; existing exam engine", flush=True)
            if "--other-skills" in sys.argv:
                if "--reading-only" not in sys.argv:
                    speaking = await client.post(
                        path + "/targeted-practice",
                        json={"client_request_id": str(uuid4()), "skill": "SPEAKING", "part": 3},
                    )
                    assert speaking.status_code == 201, speaking.text
                    print("live targeted Speaking: focused Part 3 created", flush=True)
                reading = await client.post(
                    "/api/v1/reading/sessions",
                    json={
                        "mode": "QUESTION_TYPE_PRACTICE",
                        "target_question_type": "inference",
                        "timed": False,
                    },
                )
                assert reading.status_code == 201, reading.text
                reading = reading.json()
                # Unanswered trusted questions provide real, deterministic error exposures.
                submitted = await client.post(
                    f"/api/v1/reading/sessions/{reading['id']}/submit", json={"answers": {}}
                )
                assert submitted.status_code == 200, submitted.text
                weaknesses = (await client.get("/api/v1/learning/weaknesses")).json()["items"]
                rw = next(w for w in weaknesses if w["skill"] == "READING")
                targeted_reading = await client.post(
                    f"/api/v1/learning/weaknesses/{rw['id']}/targeted-practice",
                    json={"client_request_id": str(uuid4()), "skill": "READING"},
                )
                assert targeted_reading.status_code == 201, targeted_reading.text
                rs = (
                    await client.get("/api/v1/reading/sessions/" + targeted_reading.json()["attempt_id"])
                ).json()
                assert rs["question_count"] == 10 and rs["mode"] == "QUESTION_TYPE_PRACTICE"
                print("live targeted Reading: 10 inference questions, existing Reading engine", flush=True)
            for endpoint in (
                "overview",
                "writing",
                "speaking",
                "reading",
                "grammar",
                "vocabulary",
                "today",
                "weekly",
            ):
                result = await client.get("/api/v1/learning/" + endpoint)
                assert result.status_code == 200, (endpoint, result.text)
            print("all learning dashboards: HTTP 200", flush=True)
    finally:
        if user_id:
            async with SessionLocal() as db:
                await db.execute(delete(User).where(User.id == user_id))
                await db.commit()
        await engine.dispose()
        print("disposable account cleaned", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
