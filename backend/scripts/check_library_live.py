"""Opt-in live AI smoke check. Uses and removes one disposable account; never changes existing users.
Run from backend: .venv/bin/python scripts/check_library_live.py
"""

import asyncio
import sys
from uuid import uuid4

import httpx
from sqlalchemy import delete

sys.path.insert(0, ".")
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app, hits
from app.models import User

SOURCE = """Writing Task 1
You have received this email from your friend Aldora:
Dear Alex,
I hear you are planning to visit London. I would love to meet you. When will you come, how long will you stay, and what would you like to do? Please also tell me a little about yourself so I can introduce you to my friends.
Best wishes,
Aldora
Write an email responding to Aldora.
In your email:
- Express your excitement about visiting London.
- Describe yourself.
- Say how long you will stay.
- Explain what you want to do and see.
You should write at least 120 words.
"""
ANSWER = """Dear Aldora,
Thank you for your lovely email. I am very excited about my first visit to London and I cannot wait to meet you and your friends.
As you know, I am a university student from Vietnam. I study computer science, and in my free time I enjoy reading, walking and taking photographs. I am a little shy at first, but I love meeting people from different countries.
I plan to arrive on the tenth of July and stay for about two weeks. I have already booked a small hotel near the city centre, so it should be easy for us to meet after your work.
During my stay, I would like to visit the British Museum and walk along the river. London has many famous places, and I hope you can show me your favourite park too. Please let me know which days you are free.
Best wishes,
Alex"""


async def main():
    if not settings.openai_api_key:
        print("LIVE CHECK BLOCKED: OPENAI_API_KEY is not configured", flush=True)
        return
    hits.clear()
    user_id = None
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers={"Origin": settings.frontend_url},
        timeout=660,
    ) as client:

        async def call(method, path, body=None):
            response = await client.request(method, "/api/v1" + path, json=body)
            if response.status_code >= 400:
                raise RuntimeError(f"{path}: {response.status_code} {response.text[:1000]}")
            return response.json()

        try:
            user_id = (
                await call(
                    "POST",
                    "/auth/register",
                    {"email": f"library-live-{uuid4().hex}@example.com", "password": "ExamplePassword123!"},
                )
            )["id"]
            parsed = await call("POST", "/my-questions/parse", {"text": SOURCE})
            assert parsed["items"], parsed
            doc = parsed["items"][0]["document"]
            assert doc["skill"] == "writing" and doc["part"] == "task_1", doc
            print("PASS live AI paste -> Writing Task 1 editable preview", flush=True)
            row = await call("POST", "/my-questions", {"document": doc})
            started = await call("POST", f"/my-questions/{row['id']}/practice", {})
            exam = await call("GET", f"/exams/{started['id']}")
            attempt_id = exam["attempts"][0]["id"]
            await call(
                "POST",
                f"/exams/{exam['id']}/submit",
                {"answers": {attempt_id: {"answer": ANSWER, "revision": 0}}},
            )
            print("PASS imported Writing -> existing exam submission", flush=True)
            await call("POST", f"/attempts/{attempt_id}/grade", {})
            attempt = await call("GET", f"/attempts/{attempt_id}")
            assert attempt["grading"]
            print("PASS existing AI Writing grader:", attempt["grading"]["scores"], flush=True)
            batch = await call(
                "POST",
                "/vocabulary/recommendations",
                {"source_skill": "WRITING", "source_attempt_id": attempt_id},
            )
            assert batch.get("items"), batch
            print(f"PASS Vocabulary Coach: {len(batch['items'])} items", flush=True)
            history = await call("GET", "/attempts")
            assert history["items"][0]["question"]["library_question_id"] == row["id"]
            print("PASS imported Writing history/progress linkage", flush=True)
        finally:
            if user_id:
                async with SessionLocal() as db:
                    await db.execute(delete(User).where(User.id == user_id))
                    await db.commit()
                print("Disposable live-check account removed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
