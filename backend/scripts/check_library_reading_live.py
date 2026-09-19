"""Opt-in live Reading extraction checks. Disposable account; no changes to existing content."""

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


def source(passages=1, count=10, keys=True):
    chunks = ["VSTEP Reading test" if passages == 4 else "Reading practice"]
    for index in range(passages):
        chunks.extend(
            [
                f"Reading Passage {index + 1}: Community library {index + 1}",
                f"The community library in district {index + 1} opened a quiet study room last summer. Local students can read and study there in the afternoon. The room contains science books, large tables and comfortable chairs. A volunteer helps visitors find useful information.\n\nThe library also runs a free English club every Saturday morning. Club members discuss books and practise speaking together. People of all ages can join, but they should register at the front desk before the meeting. The staff hope that the new activities will encourage more people to visit the library.",
            ]
        )
        for q in range(count):
            number = index * count + q + 1
            chunks.append(
                f"{number}. Which activity is mentioned in the passage?\nA. Practising English\nB. Buying furniture\nC. Swimming lessons\nD. Cooking meals"
            )
    if keys:
        chunks.append("Answer key: " + " ".join(f"{n}A" for n in range(1, passages * count + 1)))
    return "\n\n".join(chunks)


async def main():
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

        async def practice(doc):
            row = await call("POST", "/my-questions", {"document": doc})
            started = await call("POST", f"/my-questions/{row['id']}/practice", {})
            session = await call("GET", f"/reading/sessions/{started['id']}")
            result = await call(
                "POST",
                f"/reading/sessions/{started['id']}/submit",
                {
                    "answers": {
                        qid: {"selected_answer": "A", "revision": 0} for qid in session["question_ids"]
                    }
                },
            )
            return row, result

        try:
            user_id = (
                await call(
                    "POST",
                    "/auth/register",
                    {
                        "email": f"library-reading-live-{uuid4().hex}@example.com",
                        "password": "ExamplePassword123!",
                    },
                )
            )["id"]
            for passages, count, keys in ((1, 10, True), (1, 7, False), (4, 10, True)):
                parsed = await call("POST", "/my-questions/parse", {"text": source(passages, count, keys)})
                assert parsed["items"], parsed
                if passages == 4 and len(parsed["items"]) > 1:
                    doc = parsed["items"][0]["document"]
                    doc["part"] = "full"
                    doc["content"]["reading"] = [
                        p for item in parsed["items"] for p in item["document"]["content"]["reading"]
                    ]
                else:
                    doc = parsed["items"][0]["document"]
                questions = [q for p in doc["content"]["reading"] for q in p["questions"]]
                assert len(doc["content"]["reading"]) == passages and len(questions) == count * passages, (
                    parsed
                )
                assert all(q["correct_answer"] == ("A" if keys else None) for q in questions), parsed
                row, result = await practice(doc)
                assert result["result"]["score"] == (10 if keys else None), result
                print(
                    f"PASS live Reading paste: {passages} passage(s), {count * passages} questions, keys={keys}, score={result['result']['score']}",
                    flush=True,
                )
                if not keys:
                    for q in questions:
                        q.update(correct_answer="A", answer_key_source="user_confirmed")
                    await call("PUT", f"/my-questions/{row['id']}", {"document": doc, "expected_revision": 1})
                    started = await call("POST", f"/my-questions/{row['id']}/practice", {})
                    session = await call("GET", f"/reading/sessions/{started['id']}")
                    scored = await call(
                        "POST",
                        f"/reading/sessions/{started['id']}/submit",
                        {
                            "answers": {
                                qid: {"selected_answer": "A", "revision": 0}
                                for qid in session["question_ids"]
                            }
                        },
                    )
                    assert scored["result"]["score"] == 10
                    print("PASS explicit manual key confirmation -> new scoreable revision", flush=True)
        finally:
            if user_id:
                async with SessionLocal() as db:
                    await db.execute(delete(User).where(User.id == user_id))
                    await db.commit()
                print("Disposable Reading check account removed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
