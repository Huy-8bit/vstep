from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import DB, CurrentUser
from app.api.speaking_serializers import (
    speaking_answer_view,
    speaking_grading_view,
    speaking_question_view,
    speaking_session_view,
)
from app.common.errors import AppError
from app.core.config import settings
from app.llm.openai_client import OpenAILLMClient
from app.schemas.speaking import (
    SpeakingAdvance,
    SpeakingAnswerCreate,
    SpeakingMode,
    SpeakingQuestionRequest,
    SpeakingSessionCreate,
)
from app.services.audio_storage_service import LocalAudioStorageService
from app.services.speaking_exam_service import (
    SpeakingExamService,
    owned_speaking_answer,
    owned_speaking_session,
)
from app.services.speaking_grading_service import SpeakingGradingService
from app.services.speaking_progress_service import SpeakingProgressService
from app.services.speaking_question_generator import SpeakingQuestionGeneratorService
from app.services.speech_transcription_service import SpeechTranscriptionService
from app.services.text_to_speech_service import TextToSpeechService
from app.speech.openai_speech_client import OpenAISpeechClient

router = APIRouter(prefix="/speaking", tags=["Speaking"])


def exam_service(db):
    return SpeakingExamService(db, OpenAILLMClient(), LocalAudioStorageService())


def processor(db):
    return SpeechTranscriptionService(db, OpenAISpeechClient(), LocalAudioStorageService())


def grader(db):
    return SpeakingGradingService(db, OpenAILLMClient(), OpenAISpeechClient(), LocalAudioStorageService())


@router.get("/config")
async def config(user: CurrentUser):
    return {
        "ai_configured": bool(settings.openai_api_key),
        "audio_analysis_configured": bool(settings.openai_speaking_audio_model),
        "tts_configured": bool(settings.openai_api_key and settings.openai_tts_model),
        "max_audio_mb": settings.max_speaking_audio_mb,
        "max_audio_seconds": settings.max_speaking_audio_seconds,
    }


@router.post("/questions/generate")
async def generate(data: SpeakingQuestionRequest, db: DB, user: CurrentUser):
    return speaking_question_view(
        await SpeakingQuestionGeneratorService(db, OpenAILLMClient()).generate(data, user.id)
    )


@router.post("/sessions", status_code=201)
async def create(data: SpeakingSessionCreate, db: DB, user: CurrentUser):
    return speaking_session_view(await exam_service(db).create(data, user.id))


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: DB, user: CurrentUser):
    return speaking_session_view(await owned_speaking_session(db, session_id, user.id))


@router.post("/sessions/{session_id}/answers", status_code=201)
async def start_answer(session_id: str, data: SpeakingAnswerCreate, db: DB, user: CurrentUser):
    answer = await exam_service(db).start_answer(session_id, user.id, data.sequence_number)
    session = await owned_speaking_session(db, session_id, user.id)
    return speaking_answer_view(answer, session.mode != "FULL_TEST")


@router.post("/answers/{answer_id}/audio")
async def upload(answer_id: str, file: UploadFile, db: DB, user: CurrentUser):
    answer = await exam_service(db).upload(answer_id, user.id, file)
    session = await owned_speaking_session(db, answer.session_id, user.id)
    return speaking_answer_view(answer, session.mode != "FULL_TEST")


@router.get("/answers/{answer_id}/audio")
async def audio(answer_id: str, db: DB, user: CurrentUser):
    answer = await owned_speaking_answer(db, answer_id, user.id)
    await exam_service(db).can_review(answer, user.id)
    if not answer.audio_path:
        raise AppError(404, "Chưa có bản ghi cho câu trả lời này.")
    return FileResponse(
        LocalAudioStorageService().resolve(answer.audio_path),
        media_type=answer.mime_type,
        headers={"Cache-Control": "private, no-store"},
    )


@router.post("/answers/{answer_id}/transcribe")
async def transcribe(answer_id: str, db: DB, user: CurrentUser):
    answer = await owned_speaking_answer(db, answer_id, user.id)
    await exam_service(db).can_review(answer, user.id)
    return speaking_answer_view(await processor(db).transcribe(answer, user.id), True)


@router.post("/answers/{answer_id}/analyze")
async def analyze(answer_id: str, db: DB, user: CurrentUser, retry: bool = False):
    answer = await owned_speaking_answer(db, answer_id, user.id)
    await exam_service(db).can_review(answer, user.id)
    return speaking_answer_view(await processor(db).analyze(answer, user.id, retry), True)


@router.post("/answers/{answer_id}/grade")
async def grade_answer(answer_id: str, db: DB, user: CurrentUser):
    answer = await owned_speaking_answer(db, answer_id, user.id)
    return speaking_grading_view(await grader(db).grade(answer.session_id, user.id, answer_id))


@router.post("/sessions/{session_id}/next")
async def next_question(session_id: str, data: SpeakingAdvance, db: DB, user: CurrentUser):
    return speaking_session_view(
        await exam_service(db).advance(session_id, user.id, data.sequence_number, data.skip)
    )


@router.post("/sessions/{session_id}/complete")
async def complete(session_id: str, db: DB, user: CurrentUser):
    return speaking_session_view(await exam_service(db).complete(session_id, user.id))


@router.post("/sessions/{session_id}/grade")
async def grade_session(session_id: str, db: DB, user: CurrentUser):
    return speaking_grading_view(await grader(db).grade(session_id, user.id))


@router.get("/results/{session_id}")
async def result(session_id: str, db: DB, user: CurrentUser):
    return speaking_session_view(await owned_speaking_session(db, session_id, user.id))


@router.post("/sessions/{session_id}/tts")
async def tts(session_id: str, db: DB, user: CurrentUser):
    session = await owned_speaking_session(db, session_id, user.id)
    if session.current_sequence >= len(session.question_set):
        raise AppError(409, "Phiên đã hết câu hỏi.")
    question = session.question_set[session.current_sequence]
    spoken = ". ".join(
        filter(
            None,
            [
                question.get("situation"),
                question["question_text"],
                *question.get("options", []),
                *question.get("suggested_ideas", []),
            ],
        )
    )
    path = await TextToSpeechService(OpenAISpeechClient()).speak_question(spoken, user.id)
    return FileResponse(path, media_type="audio/mpeg", headers={"Cache-Control": "private, no-store"})


@router.get("/history")
async def history(
    db: DB,
    user: CurrentUser,
    mode: SpeakingMode | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return await SpeakingProgressService(db).history(user.id, mode, offset, limit)


@router.get("/progress")
async def progress(db: DB, user: CurrentUser, mode: SpeakingMode | None = None):
    return await SpeakingProgressService(db).progress(user.id, mode)
