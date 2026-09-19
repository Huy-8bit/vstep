"""Focused integration checks on PostgreSQL; fixtures only remove their disposable accounts."""

import io
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from PIL import Image
from sqlalchemy import delete

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app, hits
from app.models import User
from app.schemas.library import LibraryDocument, ParsedImport
from app.services.question_import_service import guard_extracted_keys, inspect_file


@pytest_asyncio.fixture
async def clients(tmp_path):
    accounts = []
    previous = settings.question_import_storage_dir
    settings.question_import_storage_dir = str(tmp_path)
    async with (
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Origin": settings.frontend_url},
        ) as first,
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Origin": settings.frontend_url},
        ) as second,
    ):
        hits.clear()
        for client in (first, second):
            result = await client.post(
                "/api/v1/auth/register",
                json={"email": f"library-check-{uuid4().hex}@example.com", "password": "ExamplePassword123!"},
            )
            assert result.status_code == 201, result.text
            accounts.append(result.json()["id"])
        yield first, second
    settings.question_import_storage_dir = previous
    async with SessionLocal() as db:
        await db.execute(delete(User).where(User.id.in_(accounts)))
        await db.commit()


def reading_document(count=7, passages=1, key=None, source="provided"):
    return LibraryDocument(
        title=f"Imported Reading {uuid4().hex[:8]}",
        skill="reading",
        part="full" if passages == 4 and count == 10 else "passage",
        content={
            "reading": [
                {
                    "title": f"A local library {i}",
                    "passage_text": f"The library in town {i} opened a study room. Students can use the room every afternoon.\n\nThe room is quiet and has books about science.",
                    "questions": [
                        {
                            "question_number": n + 1,
                            "question_text": f"Question {n + 1}: What opened in the library?",
                            "options": {"A": "A study room", "B": "A shop", "C": "A pool", "D": "A cinema"},
                            "correct_answer": key,
                            "answer_key_source": source if key else "unknown",
                        }
                        for n in range(count)
                    ],
                }
                for i in range(passages)
            ]
        },
    ).model_dump()


async def save(client, document):
    response = await client.post("/api/v1/my-questions", json={"document": document})
    assert response.status_code == 201, response.text
    return response.json()


async def start(client, row, revision=None):
    response = await client.post(f"/api/v1/my-questions/{row['id']}/practice", json={"revision": revision})
    assert response.status_code == 201, response.text
    return response.json()


async def test_reading_incomplete_keys_revision_retry_and_analytics(clients):
    client, other = clients
    row = await save(client, reading_document())
    started = await start(client, row)
    session = (await client.get(f"/api/v1/reading/sessions/{started['id']}")).json()
    assert session["question_count"] == 7
    assert session["library_question_id"] == row["id"]
    assert "correct_answer" not in session["passages"][0]["questions"][0]
    assert (await client.get(f"/api/v1/reading/results/{started['id']}")).status_code == 409
    answers = {qid: {"selected_answer": "A", "revision": 0} for qid in session["question_ids"]}
    result = await client.post(f"/api/v1/reading/sessions/{started['id']}/submit", json={"answers": answers})
    assert result.status_code == 200, result.text
    result = result.json()
    assert result["result"]["score"] is None
    assert result["result"]["incorrect_count"] == result["result"]["unanswered_count"] == 0
    assert result["result"]["unscored_count"] == 7
    assert all(q["is_correct"] is None for q in result["review"])
    progress = (await client.get("/api/v1/reading/progress")).json()
    assert (
        progress["average_score"] is None
        and progress["questions_answered"] == 7
        and progress["accuracy"] is None
    )
    doc = row["document"]
    for q in doc["content"]["reading"][0]["questions"]:
        q.update(correct_answer="A", answer_key_source="user_confirmed")
    update = await client.put(
        f"/api/v1/my-questions/{row['id']}", json={"document": doc, "expected_revision": 1}
    )
    assert update.status_code == 200, update.text
    assert update.json()["revision"] == 2
    old = await start(client, row, 1)
    old_session = (await client.get(f"/api/v1/reading/sessions/{old['id']}")).json()
    assert old_session["question_ids"] == session["question_ids"]
    fresh = await start(client, row)
    fresh_session = (await client.get(f"/api/v1/reading/sessions/{fresh['id']}")).json()
    assert fresh_session["question_ids"] != session["question_ids"]
    result = await client.post(
        f"/api/v1/reading/sessions/{fresh['id']}/submit",
        json={
            "answers": {qid: {"selected_answer": "A", "revision": 0} for qid in fresh_session["question_ids"]}
        },
    )
    assert result.status_code == 200, result.text
    assert result.json()["result"]["score"] == 10
    progress = (await client.get("/api/v1/reading/progress")).json()
    assert progress["average_score"] == 10 and progress["accuracy"] == 100 and progress["unscored_count"] == 7
    stats = (await client.get(f"/api/v1/my-questions/{row['id']}")).json()["stats"]
    assert stats["attempt_count"] == 3 and stats["best_score"] == 10
    assert (await other.get(f"/api/v1/my-questions/{row['id']}")).status_code == 404
    assert (await other.post(f"/api/v1/my-questions/{row['id']}/practice", json={})).status_code == 404
    assert (await other.get(f"/api/v1/reading/passages/{session['passages'][0]['id']}")).status_code == 404
    assert (await other.get("/api/v1/my-questions")).json()["total"] == 0
    bank = (await other.get("/api/v1/reading/bank")).json()["items"]
    assert session["passages"][0]["id"] not in {p["id"] for p in bank}
    assert (await client.delete(f"/api/v1/my-questions/{row['id']}")).status_code == 204
    assert (await client.get(f"/api/v1/reading/results/{started['id']}")).json()["result"]["score"] is None
    await start(client, row, 1)  # History can retry its frozen revision after soft deletion.


async def test_full_reading_and_unconfirmed_keys(clients):
    client, _ = clients
    row = await save(client, reading_document(10, 4, "A"))
    started = await start(client, row)
    session = (await client.get(f"/api/v1/reading/sessions/{started['id']}")).json()
    assert (
        session["mode"] == "FULL_TEST"
        and len(session["passages"]) == 4
        and len(session["question_ids"]) == 40
        and session["expires_at"]
    )
    assert [q["question_number"] for p in session["passages"] for q in p["questions"]] == list(range(1, 41))
    result = await client.post(
        f"/api/v1/reading/sessions/{started['id']}/submit",
        json={
            "answers": {
                qid: {"selected_answer": "A" if i % 2 == 0 else "B", "revision": 0}
                for i, qid in enumerate(session["question_ids"])
            }
        },
    )
    assert result.json()["result"]["score"] == 5
    row = await save(client, reading_document(1, 1, "A", "ai_suggested"))
    started = await start(client, row)
    result = await client.post(f"/api/v1/reading/sessions/{started['id']}/submit", json={"answers": {}})
    assert result.json()["result"]["score"] is None


async def test_writing_exact_prompt_private_duplicate_and_snapshot(clients):
    client, other = clients
    doc = LibraryDocument(
        title="Visit to London",
        skill="writing",
        part="task_1",
        source_type="copied_text",
        content={
            "writing": [
                {
                    "task_type": 1,
                    "instruction": "Write a letter responding to Aldora.",
                    "stimulus_type": "letter",
                    "stimulus_text": "Dear Alex,\nCan you visit London?\nAldora",
                    "requirements": [
                        "Express your excitement",
                        "Describe yourself",
                        "Say how long you will stay",
                        "Explain what you want to see",
                    ],
                    "minimum_words": 100,
                }
            ]
        },
    ).model_dump()
    row = await save(client, doc)
    same = {**doc, "title": "Same prompt, other title"}
    response = await client.post("/api/v1/my-questions", json={"document": same})
    assert response.status_code == 409 and response.json()["duplicate"]["id"] == row["id"]
    started = await start(client, row)
    assert started["url"].startswith("/exam/")
    exam = (await client.get(f"/api/v1/exams/{started['id']}")).json()
    question = exam["attempts"][0]["question"]
    assert question["stimulus"] == doc["content"]["writing"][0]["stimulus_text"]
    assert question["requirements"] == doc["content"]["writing"][0]["requirements"]
    assert question["minimum_words"] == 100
    assert (await other.get(f"/api/v1/questions/{question['id']}")).status_code == 404
    assert (
        await other.post("/api/v1/exams", json={"mode": "TASK1", "question_ids": [question["id"]]})
    ).status_code == 422
    doc["content"]["writing"][0]["instruction"] = "Changed instruction for the next attempt."
    assert (
        await client.put(f"/api/v1/my-questions/{row['id']}", json={"document": doc, "expected_revision": 1})
    ).status_code == 200
    assert (await client.get(f"/api/v1/exams/{started['id']}")).json()["attempts"][0]["question"][
        "instruction"
    ] == "Write a letter responding to Aldora."
    assert (await client.get("/api/v1/attempts")).json()["items"][0]["question"][
        "library_question_id"
    ] == row["id"]


async def test_full_speaking_uses_existing_sequential_engine(clients):
    client, other = clients
    doc = LibraryDocument(
        title="My speaking exam",
        skill="speaking",
        part="full",
        content={
            "speaking": [
                {
                    "part": 1,
                    "topic_sets": [
                        {"topic": "Sport", "questions": ["Do you like sports?", "Which sport do you play?"]}
                    ],
                },
                {
                    "part": 2,
                    "situation": "Your friend wants to improve English this summer.",
                    "options": ["Take a course", "Use an application", "Join a club"],
                    "candidate_task": "Choose the best option and explain why.",
                    "optional_context": "Your friend has a limited budget.",
                },
                {
                    "part": 3,
                    "central_idea": "Learning languages has many benefits.",
                    "suggested_ideas": ["Jobs", "Communication", "Culture"],
                    "follow_up_questions": ["Should children learn languages early?"],
                },
            ]
        },
    ).model_dump()
    row = await save(client, doc)
    started = await start(client, row)
    session = (await client.get(f"/api/v1/speaking/sessions/{started['id']}")).json()
    assert session["mode"] == "FULL_TEST" and session["total_questions"] == 5
    assert session["current_question"]["question_text"] == "Do you like sports?"
    assert len(session["visible_questions"]) == 1
    assert (await other.get(f"/api/v1/speaking/sessions/{started['id']}")).status_code == 404

    observed = []
    for number in range(session["total_questions"]):
        current = (await client.get(f"/api/v1/speaking/sessions/{started['id']}")).json()
        observed.append(current["current_question"]["part"])
        assert current["current_question"]["sequence_number"] == number
        advanced = await client.post(
            f"/api/v1/speaking/sessions/{started['id']}/next", json={"sequence_number": number, "skip": True}
        )
        assert advanced.status_code == 200, advanced.text
    assert observed == [1, 1, 2, 3, 3]
    complete = await client.post(f"/api/v1/speaking/sessions/{started['id']}/complete")
    assert complete.status_code == 200 and complete.json()["status"] == "COMPLETED"
    assert len(complete.json()["visible_questions"]) == session["total_questions"]


async def test_private_upload_and_multi_item_parse_preview(clients, monkeypatch):
    client, other = clients
    from app.llm.openai_client import OpenAILLMClient

    async def parse(self, payload, user_id, media=None):
        assert media and media[0]["type"] == "input_image"
        return ParsedImport.model_validate(
            {
                "items": [
                    {
                        "title": "Summer study",
                        "skill": "speaking",
                        "part": "part_2",
                        "topic": "education",
                        "tags": [],
                        "content": {
                            "speaking": [
                                {
                                    "part": 2,
                                    "situation": "Your friend wants to study English.",
                                    "options": ["A course", "an app", "a club"],
                                    "candidate_task": "Choose the best option.",
                                }
                            ]
                        },
                        "skill_confidence": 0.99,
                        "part_confidence": 0.99,
                        "warnings": [],
                    }
                ],
                "warnings": [],
            }
        )

    monkeypatch.setattr(OpenAILLMClient, "parse_library_question", parse)
    blob = io.BytesIO()
    Image.new("RGB", (100, 100), "white").save(blob, format="PNG")
    uploaded = await client.post(
        "/api/v1/my-questions/assets", files={"file": ("speaking.png", blob.getvalue(), "image/png")}
    )
    assert uploaded.status_code == 201, uploaded.text
    asset_id = uploaded.json()["id"]
    assert (await other.get(f"/api/v1/my-questions/assets/{asset_id}")).status_code == 404
    result = await client.post("/api/v1/my-questions/parse", json={"asset_id": asset_id})
    assert result.status_code == 200, result.text
    assert (await client.get("/api/v1/my-questions")).json()["total"] == 0
    document = result.json()["items"][0]["document"]
    document["content"]["speaking"][0]["options"][1] = "An online application"
    row = await save(client, document)
    assert row["document"]["asset_ids"] == [asset_id]
    assert (await other.post("/api/v1/my-questions", json={"document": document})).status_code == 404
    await start(client, row)
    assert (
        await client.post(
            "/api/v1/my-questions/assets", files={"file": ("fake.png", b"<html>bad</html>", "image/png")}
        )
    ).status_code == 422


def test_parser_drops_unverifiable_answer_keys():
    document = reading_document(3, 1, "A")
    item = {key: document[key] for key in ("title", "skill", "part", "topic", "tags", "content")}
    item.update(skill_confidence=0.95, part_confidence=0.9, warnings=[])
    questions = item["content"]["reading"][0]["questions"]
    questions[0]["answer_key_evidence"] = "1. A"
    questions[1]["answer_key_evidence"] = "2. A"  # fabricated citation
    result = guard_extracted_keys(
        ParsedImport.model_validate({"items": [item], "warnings": []}), "Explicit answer key: 1. A"
    )
    assert [q.correct_answer for q in result.items[0].content.reading[0].questions] == ["A", None, None]


def test_pdf_validation_rejects_encrypted_and_too_many_pages():
    from pypdf import PdfWriter

    from app.common.errors import AppError

    writer = PdfWriter()
    for _ in range(21):
        writer.add_blank_page(100, 100)
    blob = io.BytesIO()
    writer.write(blob)
    with pytest.raises(AppError):
        inspect_file(blob.getvalue(), "large.pdf", "application/pdf")
    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    writer.encrypt("secret")
    blob = io.BytesIO()
    writer.write(blob)
    with pytest.raises(AppError):
        inspect_file(blob.getvalue(), "locked.pdf", "application/pdf")


def test_parser_removes_invented_content_and_preserves_supplied_wording():
    from app.validators.library_import import guard_source_wording

    parsed = ParsedImport.model_validate(
        {
            "items": [
                {
                    "title": "English summer",
                    "skill": "speaking",
                    "part": "part_2",
                    "topic": "education",
                    "tags": [],
                    "content": {
                        "speaking": [
                            {
                                "part": 2,
                                "situation": "Your friend wants to study English.",
                                "options": ["A course", "an app", "a fabricated third option"],
                                "candidate_task": "Invented candidate task",
                            }
                        ]
                    },
                    "skill_confidence": 0.9,
                    "part_confidence": 0.9,
                    "warnings": [],
                }
            ],
            "warnings": [],
        }
    )
    result = guard_source_wording(parsed, "Your friend wants to study English. Options: A course, an app.")
    item = result.items[0].content.speaking[0]
    assert item.options == ["A course", "an app", ""]
    assert item.candidate_task == "" and result.items[0].warnings


async def test_reading_preserves_source_order_and_organization(clients):
    client, other = clients
    doc = reading_document(2, 1, "A")
    first, second = doc["content"]["reading"][0]["questions"]
    first["question_number"], second["question_number"] = 5, 3
    row = await save(client, doc)
    started = await start(client, row)
    session = (await client.get(f"/api/v1/reading/sessions/{started['id']}")).json()
    questions = session["passages"][0]["questions"]
    assert [q["source_question_number"] for q in questions] == [5, 3]
    assert [q["question_text"] for q in questions] == [first["question_text"], second["question_text"]]
    collection = (
        await client.post("/api/v1/my-questions/collections", json={"name": "Teacher's questions"})
    ).json()
    organized = await client.patch(
        f"/api/v1/my-questions/{row['id']}",
        json={"collection_id": collection["id"], "favorite": True, "tags": ["teacher"]},
    )
    assert organized.status_code == 200, organized.text
    assert (
        await client.get(
            f"/api/v1/my-questions?favorite=true&tag=teacher&practiced=true&collection_id={collection['id']}"
        )
    ).json()["total"] == 1
    other_doc = reading_document(1)
    other_doc["collection_id"] = collection["id"]
    assert (await other.post("/api/v1/my-questions", json={"document": other_doc})).status_code == 404
