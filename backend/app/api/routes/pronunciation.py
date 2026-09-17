from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import DB, CurrentUser
from app.common.errors import AppError
from app.schemas.audio_assessment import PronunciationCreate
from app.services.audio_storage_service import LocalAudioStorageService
from app.services.pronunciation_practice_service import PronunciationPracticeService, practice_view
from app.services.text_to_speech_service import TextToSpeechService
from app.speech.openai_audio_analysis import OpenAIAudioAnalysisProvider
from app.speech.openai_speech_client import OpenAISpeechClient

router = APIRouter(prefix="/speaking/pronunciation", tags=["Pronunciation"])


def service(db):
    return PronunciationPracticeService(db, LocalAudioStorageService(), OpenAIAudioAnalysisProvider())


@router.post("/practices", status_code=201)
async def create(data: PronunciationCreate, db: DB, user: CurrentUser):
    return practice_view(await service(db).create(data, user.id))


@router.get("/practices/{identifier}")
async def get_practice(identifier: str, db: DB, user: CurrentUser):
    return practice_view(await service(db).owned(identifier, user.id))


@router.post("/practices/{identifier}/audio")
async def upload(identifier: str, file: UploadFile, db: DB, user: CurrentUser):
    return practice_view(await service(db).upload(identifier, user.id, file))


@router.get("/practices/{identifier}/audio")
async def audio(identifier: str, db: DB, user: CurrentUser):
    item = await service(db).owned(identifier, user.id)
    if not item.audio_path:
        raise AppError(404, "Lượt luyện chưa có bản ghi.")
    return FileResponse(
        LocalAudioStorageService().resolve(item.audio_path),
        media_type="audio/wav",
        headers={"Cache-Control": "private, no-store"},
    )


@router.post("/practices/{identifier}/analyze")
async def analyze(identifier: str, db: DB, user: CurrentUser):
    return practice_view(await service(db).analyze(identifier, user.id))


@router.post("/practices/{identifier}/tts")
async def tts(identifier: str, db: DB, user: CurrentUser):
    item = await service(db).owned(identifier, user.id)
    path = await TextToSpeechService(OpenAISpeechClient(), db).speak_question(item.reference_text, user.id)
    return FileResponse(path, media_type="audio/mpeg", headers={"Cache-Control": "private, no-store"})


@router.get("/history")
async def history(
    db: DB,
    user: CurrentUser,
    reference_hash: str | None = Query(None, pattern=r"^[0-9a-f]{64}$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return await service(db).history(user.id, reference_hash, offset, limit)


@router.get("/progress")
async def progress(db: DB, user: CurrentUser):
    return await service(db).progress(user.id)
