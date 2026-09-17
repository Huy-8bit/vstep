from sqlalchemy import select

from app.common.errors import AppError
from app.models import ExamSession, WritingAttempt


async def owned_exam(db, exam_id: str, user_id: str, lock: bool = False) -> ExamSession:
    query = select(ExamSession).where(ExamSession.id == exam_id, ExamSession.user_id == user_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    exam = await db.scalar(query)
    if not exam:
        raise AppError(404, "Không tìm thấy phiên luyện tập.")
    return exam


async def owned_attempt(db, attempt_id: str, user_id: str) -> WritingAttempt:
    attempt = await db.scalar(
        select(WritingAttempt).where(WritingAttempt.id == attempt_id, WritingAttempt.user_id == user_id)
    )
    if not attempt:
        raise AppError(404, "Không tìm thấy bài làm.")
    return attempt
