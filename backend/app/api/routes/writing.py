from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser
from app.api.serializers import attempt_view, exam_view, question_view
from app.common.errors import AppError
from app.llm.openai_client import OpenAILLMClient
from app.models import ExamSession, WritingAttempt, WritingQuestion
from app.repositories.writing import owned_attempt
from app.schemas.api import AnswerUpdate, ExamCreate, ExamSubmit
from app.schemas.writing import QuestionRequest
from app.services.exam_service import ExamService
from app.services.question_generator import QuestionGeneratorService
from app.services.writing_grader import WritingGradingService

router = APIRouter(tags=["Writing"])


def get_llm():
    return OpenAILLMClient()


@router.post("/questions/generate")
async def generate(data: QuestionRequest, db: DB, user: CurrentUser):
    return question_view(await QuestionGeneratorService(db, get_llm()).generate(data, user.id))


@router.get("/questions/{question_id}")
async def question(question_id: str, db: DB, user: CurrentUser):
    q = await db.get(WritingQuestion, question_id)
    if not q:
        raise AppError(404, "Không tìm thấy đề bài.")
    return question_view(q)


@router.post("/exams", status_code=201)
async def create_exam(data: ExamCreate, db: DB, user: CurrentUser):
    return exam_view(await ExamService(db, get_llm()).create(data, user.id))


@router.get("/exams/{exam_id}")
async def get_exam(exam_id: str, db: DB, user: CurrentUser):
    return exam_view(await ExamService(db, get_llm()).get(exam_id, user.id))


@router.post("/exams/{exam_id}/submit")
async def submit_exam(exam_id: str, data: ExamSubmit, db: DB, user: CurrentUser):
    return exam_view(await ExamService(db, get_llm()).submit(exam_id, user.id, data))


@router.patch("/attempts/{attempt_id}")
async def save_attempt(attempt_id: str, data: AnswerUpdate, db: DB, user: CurrentUser):
    return attempt_view(await ExamService(db, get_llm()).save(attempt_id, user.id, data))


@router.post("/attempts/{attempt_id}/submit")
async def submit_attempt(attempt_id: str, data: AnswerUpdate, db: DB, user: CurrentUser):
    a = await owned_attempt(db, attempt_id, user.id)
    e = await db.get(ExamSession, a.exam_session_id)
    if e.mode == "FULL_TEST":
        raise AppError(409, "Hãy nộp cả hai Task qua phiên thi Writing.", "full_exam_required")
    exam = await ExamService(db, get_llm()).submit(e.id, user.id, ExamSubmit(answers={a.id: data}))
    return attempt_view(exam.attempts[0])


@router.post("/attempts/{attempt_id}/grade")
async def grade_attempt(attempt_id: str, db: DB, user: CurrentUser):
    return attempt_view(await WritingGradingService(db, get_llm()).grade(attempt_id, user.id))


@router.get("/attempts")
async def history(
    db: DB,
    user: CurrentUser,
    mode: Literal["FULL_TEST", "TASK1", "TASK2"] | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    query = select(WritingAttempt).join(ExamSession).where(WritingAttempt.user_id == user.id)
    if mode:
        query = query.where(ExamSession.mode == mode)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    attempts = list(
        await db.scalars(query.order_by(WritingAttempt.created_at.desc()).offset(offset).limit(limit))
    )
    modes = dict(
        (
            await db.execute(
                select(ExamSession.id, ExamSession.mode).where(
                    ExamSession.id.in_({a.exam_session_id for a in attempts})
                )
            )
        ).all()
    )
    return {
        "total": total,
        "items": [{**attempt_view(a), "mode": modes[a.exam_session_id]} for a in attempts],
    }


@router.get("/attempts/{attempt_id}")
async def get_attempt(attempt_id: str, db: DB, user: CurrentUser):
    a = await owned_attempt(db, attempt_id, user.id)
    exam = await ExamService(db, get_llm()).get(a.exam_session_id, user.id)
    return {**attempt_view(a), "exam": exam_view(exam)}
