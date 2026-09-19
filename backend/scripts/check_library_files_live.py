"""Live image/PDF + Speaking audio integration check with synthetic, clearly identified fixtures.
Run inside backend container (ffmpeg is required). One disposable account, no existing user content.
"""

import asyncio
import io
import sys
import tempfile
from uuid import uuid4

import httpx
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import delete

sys.path.insert(0, ".")
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app, hits
from app.models import User
from app.speech.openai_speech_client import OpenAISpeechClient

LINES = [
    "VSTEP SPEAKING PART 2",
    "",
    "Your friend wants to improve his English this summer.",
    "He has a limited budget and is free at weekends.",
    "",
    "Three options:",
    "1. Attend an English course",
    "2. Study with an online aplication",
    "3. Join an English club",
    "",
    "Choose the best option and explain your choice.",
    "Explain why the other two options are less suitable.",
]
SPOKEN = """I think joining an English club would be the best choice for my friend. First of all, he has a limited budget, and many local clubs are free or very cheap. He can attend meetings at weekends, so they fit his schedule. More importantly, he will have the chance to practise speaking with other learners in a friendly environment. An English course could provide more structured lessons, but it might be too expensive for him this summer. An online application is convenient and useful for learning vocabulary. However, it does not always provide enough real conversation. For these reasons, I would recommend the club. He could also use a free application at home to review what he learns during the meetings."""


def fixture_bytes(format):
    image = Image.new("RGB", (1200, 750), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=26)
    for i, line in enumerate(LINES):
        draw.text((35, 35 + 45 * i), line, fill="black", font=font)
    stream = io.BytesIO()
    image.save(stream, format=format)
    return stream.getvalue()


async def main():
    if not settings.openai_api_key:
        print("LIVE CHECK BLOCKED: OpenAI key missing", flush=True)
        return
    hits.clear()
    user_id = None
    original_files, original_audio = settings.question_import_storage_dir, settings.audio_storage_dir
    with tempfile.TemporaryDirectory(prefix="library-live-") as folder:
        settings.question_import_storage_dir = folder + "/imports"
        settings.audio_storage_dir = folder + "/audio"
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers={"Origin": settings.frontend_url},
            timeout=660,
        ) as client:

            async def call(method, path, body=None, files=None):
                response = await client.request(
                    method, "/api/v1" + path, **({"files": files} if files else {"json": body})
                )
                if response.status_code >= 400:
                    raise RuntimeError(f"{path}: {response.status_code} {response.text[:1200]}")
                return response.json()

            try:
                user_id = (
                    await call(
                        "POST",
                        "/auth/register",
                        {
                            "email": f"library-files-live-{uuid4().hex}@example.com",
                            "password": "ExamplePassword123!",
                        },
                    )
                )["id"]
                image_asset = await call(
                    "POST",
                    "/my-questions/assets",
                    files={"file": ("speaking.png", fixture_bytes("PNG"), "image/png")},
                )
                parsed = await call("POST", "/my-questions/parse", {"asset_id": image_asset["id"]})
                doc = parsed["items"][0]["document"]
                assert doc["skill"] == "speaking" and doc["part"] == "part_2", doc
                question = doc["content"]["speaking"][0]
                assert len(question["options"]) == 3 and "English" in question["situation"], question
                question["options"][1] = "Study with an online application"
                doc["content"]["practice_asset_ids"] = [image_asset["id"]]
                print(
                    "PASS live image extraction -> editable Speaking Part 2, 3 options, typo corrected",
                    flush=True,
                )
                row = await call("POST", "/my-questions", {"document": doc})
                started = await call("POST", f"/my-questions/{row['id']}/practice", {})
                session = await call("GET", f"/speaking/sessions/{started['id']}")
                assert session["current_question"]["options"][1] == question["options"][1]
                answer = await call(
                    "POST", f"/speaking/sessions/{started['id']}/answers", {"sequence_number": 0}
                )
                print(
                    "Generating synthetic speech solely to check the audio pipeline (not microphone capture)",
                    flush=True,
                )
                audio = await OpenAISpeechClient().synthesize(SPOKEN, user_id)
                uploaded = await call(
                    "POST",
                    f"/speaking/answers/{answer['id']}/audio",
                    files={"file": ("fixture.mp3", audio, "audio/mpeg")},
                )
                assert uploaded["has_audio"], uploaded
                transcript = await call("POST", f"/speaking/answers/{answer['id']}/transcribe", {})
                assert transcript["transcript"], transcript
                print(
                    "PASS imported Speaking -> existing audio upload/normalization/transcription", flush=True
                )
                await call(
                    "POST", f"/speaking/sessions/{started['id']}/next", {"sequence_number": 0, "skip": False}
                )
                await call("POST", f"/speaking/sessions/{started['id']}/complete", {})
                await call("POST", f"/speaking/sessions/{started['id']}/grade", {})
                result = await call("GET", f"/speaking/results/{started['id']}")
                assert result["grading"], result
                analysis = result["answers"][0]["audio_analysis"]
                assert (
                    analysis and analysis.get("available") and analysis.get("pronunciation_score") is not None
                ), analysis
                print("PASS existing Speaking grader + audio-based pronunciation assessment", flush=True)
                batch = await call(
                    "POST",
                    "/vocabulary/recommendations",
                    {"source_skill": "SPEAKING", "source_attempt_id": started["id"]},
                )
                assert batch.get("items"), batch
                print(f"PASS Speaking Vocabulary Coach: {len(batch['items'])} items", flush=True)
                pdf_asset = await call(
                    "POST",
                    "/my-questions/assets",
                    files={"file": ("speaking.pdf", fixture_bytes("PDF"), "application/pdf")},
                )
                pdf = await call("POST", "/my-questions/parse", {"asset_id": pdf_asset["id"]})
                assert pdf["items"] and pdf["items"][0]["document"]["skill"] == "speaking", pdf
                print("PASS live PDF direct input -> structured editable preview", flush=True)
            finally:
                settings.question_import_storage_dir, settings.audio_storage_dir = (
                    original_files,
                    original_audio,
                )
                if user_id:
                    async with SessionLocal() as db:
                        await db.execute(delete(User).where(User.id == user_id))
                        await db.commit()
                    print("Disposable account and fixture files removed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
