"""Check Next's HTTP proxy and real persistent upload storage with one disposable account.
Run inside backend container: python scripts/check_library_http.py
"""

import asyncio
import io
import sys
from pathlib import Path
from uuid import uuid4

import httpx
from PIL import Image
from sqlalchemy import delete, select

sys.path.insert(0, ".")
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import User
from app.models.library import QuestionImportFile


async def main():
    user_id = None
    async with httpx.AsyncClient(
        base_url="http://frontend:3000", headers={"Origin": settings.frontend_url}, timeout=60
    ) as client:

        async def call(method, path, **kwargs):
            response = await client.request(method, "/api/v1" + path, **kwargs)
            assert response.status_code < 400, (path, response.status_code, response.text[:600])
            return response

        try:
            user_id = (
                await call(
                    "POST",
                    "/auth/register",
                    json={
                        "email": f"library-http-{uuid4().hex}@example.com",
                        "password": "ExamplePassword123!",
                    },
                )
            ).json()["id"]
            stream = io.BytesIO()
            Image.new("RGB", (100, 60), "white").save(stream, format="PNG")
            asset = (
                await call(
                    "POST",
                    "/my-questions/assets",
                    files={"file": ("source.png", stream.getvalue(), "image/png")},
                )
            ).json()
            downloaded = await call("GET", f"/my-questions/assets/{asset['id']}")
            assert downloaded.content == stream.getvalue()
            document = {
                "title": "HTTP library check",
                "skill": "writing",
                "part": "task_1",
                "asset_ids": [asset["id"]],
                "content": {
                    "practice_asset_ids": [asset["id"]],
                    "writing": [{"task_type": 1, "instruction": "Write a letter to your friend."}],
                },
            }
            row = (await call("POST", "/my-questions", json={"document": document})).json()
            assert (await client.get("/my-questions")).status_code == 200
            await call("PATCH", f"/my-questions/{row['id']}", json={"favorite": True})
            await call("DELETE", f"/my-questions/{row['id']}")
            print(
                "PASS real Next HTTP proxy: authenticated list/create/favorite/delete and byte-exact private upload/download",
                flush=True,
            )
        finally:
            if user_id:
                async with SessionLocal() as db:
                    paths = list(
                        await db.scalars(
                            select(QuestionImportFile.path).where(QuestionImportFile.user_id == user_id)
                        )
                    )
                    await db.execute(delete(User).where(User.id == user_id))
                    await db.commit()
                for path in paths:
                    Path(path).unlink(missing_ok=True)
                folder = Path(settings.question_import_storage_dir) / user_id
                if folder.exists():
                    folder.rmdir()
                print("Disposable account and uploaded fixture removed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
