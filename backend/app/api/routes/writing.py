from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import DB, CurrentUser
from app.api.serializers import attempt_view, exam_view, grading_view, question_view
from app.common.errors import AppError
from app.core.config import settings
from app.llm.openai_client import OpenAILLMClient
from app.models import ExamSession, WritingAttempt, WritingQuestion
from app.models.assessment import WritingGradingRevision
from app.repositories.writing import owned_attempt
from app.schemas.api import AnswerUpdate, ExamCreate, ExamSubmit
from app.schemas.writing import QuestionRequest
from app.services.entitlements import EntitlementService, writing_feature
from app.services.exam_service import ExamService
from app.services.question_generator import QuestionGeneratorService
from app.services.writing_grader import WritingGradingService

router = APIRouter(tags=["Writing"])


def get_llm():
    return OpenAILLMClient()


@router.post("/questions/generate")
async def generate(data: QuestionRequest, db: DB, user: CurrentUser):
    access = EntitlementService(db)
    decision = await access.require(user, writing_feature(f"TASK{data.task}"))
    if data.source == "AI":
        await access.require(user, "AI_GENERATION", consume=True)
    return question_view(await QuestionGeneratorService(db, get_llm()).generate(data, user.id, trial_only=decision.reason == "TRIAL_AVAILABLE", publish_global=user.role == "ADMIN"))


@router.get("/questions/{question_id}")
async def question(question_id: str, db: DB, user: CurrentUser):
    q = await db.get(WritingQuestion, question_id)
    if not q or q.owner_id not in (None, user.id) or (q.owner_id is None and (not q.is_published or q.access_tier == "INTERNAL")):
        raise AppError(404, "Không tìm thấy đề bài.")
    if q.owner_id is None and user.role != "ADMIN" and not await EntitlementService(db).vip_expiry(user.id):
        used_here = await db.scalar(select(WritingAttempt.id).where(WritingAttempt.user_id == user.id, WritingAttempt.question_id == q.id).limit(1))
        remaining = await EntitlementService(db).quota.trial_remaining(user.id, "WRITING_TASK1")
        if not used_here and not (q.task_type == 1 and q.available_for_free_trial and remaining):
            raise AppError(403, "Nâng cấp VIP để xem đề này.", "VIP_REQUIRED")
    return question_view(q)


@router.post("/exams", status_code=201)
async def create_exam(data: ExamCreate, db: DB, user: CurrentUser):
    decision = await EntitlementService(db).require(user, writing_feature(data.mode), consume=True)
    return exam_view(await ExamService(db, get_llm()).create(data, user.id, trial_only=decision.reason == "TRIAL_AVAILABLE", access_source="ADMIN" if user.role == "ADMIN" else "TRIAL" if decision.reason == "TRIAL_AVAILABLE" else "VIP"))


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
    a = await owned_attempt(db, attempt_id, user.id)
    exam = await db.get(ExamSession, a.exam_session_id)
    await EntitlementService(db).require_existing(user, writing_feature(exam.mode), exam.access_source)
    return attempt_view(await WritingGradingService(db, get_llm()).grade(attempt_id, user.id))


@router.post("/attempts/{attempt_id}/analyze")
async def analyze_attempt(attempt_id: str, db: DB, user: CurrentUser, upgrade: bool = False):
    await EntitlementService(db).require(user, "WRITING_FULL")
    return await WritingGradingService(db, get_llm()).analyze(attempt_id, user.id, upgrade)


@router.post("/attempts/{attempt_id}/calibrate")
async def calibrate_attempt(attempt_id: str, db: DB, user: CurrentUser, upgrade: bool = False):
    await EntitlementService(db).require(user, "WRITING_FULL")
    return await WritingGradingService(db, get_llm()).calibrate(attempt_id, user.id, upgrade)


@router.post("/attempts/{attempt_id}/feedback")
async def prepare_feedback(attempt_id: str, db: DB, user: CurrentUser, upgrade: bool = False):
    await EntitlementService(db).require(user, "WRITING_FULL")
    return await WritingGradingService(db, get_llm()).prepare_feedback(attempt_id, user.id, upgrade)


@router.post("/attempts/{attempt_id}/vocabulary")
async def prepare_vocabulary(attempt_id: str, db: DB, user: CurrentUser, upgrade: bool = False):
    await EntitlementService(db).require(user, "VOCABULARY")
    return await WritingGradingService(db, get_llm()).prepare_vocabulary(attempt_id, user.id, upgrade)


@router.post("/attempts/{attempt_id}/regrade")
async def regrade_attempt(attempt_id: str, db: DB, user: CurrentUser):
    await EntitlementService(db).require(user, "WRITING_FULL")
    return attempt_view(await WritingGradingService(db, get_llm()).grade(attempt_id, user.id, upgrade=True))


@router.post("/attempts/{attempt_id}/optional-feedback/{kind}")
async def optional_feedback(
    attempt_id: str,
    kind: Literal["sentences", "corrected", "improved", "detailed"],
    db: DB,
    user: CurrentUser,
):
    await EntitlementService(db).require(user, "WRITING_FULL")
    from app.services.writing_optional_feedback import WritingOptionalFeedbackService

    return attempt_view(
        await WritingOptionalFeedbackService(db, get_llm()).generate(attempt_id, user.id, kind)
    )


@router.get("/attempts/{attempt_id}/grading-history")
async def grading_history(attempt_id: str, db: DB, user: CurrentUser):
    attempt = await owned_attempt(db, attempt_id, user.id)
    revisions = await db.scalars(
        select(WritingGradingRevision)
        .where(WritingGradingRevision.attempt_id == attempt.id)
        .order_by(WritingGradingRevision.created_at.desc())
    )
    return {
        "current": grading_view(attempt.grading),
        "previous": [{"id": r.id, "grading": r.snapshot} for r in revisions],
    }


@router.get("/internal/writing-calibration/{attempt_id}")
async def inspect_calibration(attempt_id: str, db: DB, user: CurrentUser):
    admins = {
        email.strip().lower()
        for email in settings.writing_calibration_admin_emails.split(",")
        if email.strip()
    }
    if user.role != "ADMIN" or user.email.lower() not in admins:
        raise AppError(404, "Không tìm thấy trang kiểm tra hiệu chỉnh.")
    attempt = await db.scalar(select(WritingAttempt).where(WritingAttempt.id == attempt_id))
    if not attempt:
        raise AppError(404, "Không tìm thấy bài viết.")
    return {"attempt": attempt_view(attempt), "work": attempt.grading_work}


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
