from sqlalchemy import select

from app.models import ExamSession
from app.models.reading import ReadingExamSession
from app.models.speaking import SpeakingExamSession
from app.repositories.library import document_view
from app.schemas.library import LibraryDocument, practice_issues


def library_view(row, stats=None, *, include_content=True):
    document = document_view(row)
    if not include_content:
        document.pop("content")
    parsed = LibraryDocument.model_validate(document_view(row))
    reading = [q for p in parsed.content.reading for q in p.questions]
    trusted = sum(
        q.correct_answer is not None and q.answer_key_source in ("provided", "user_confirmed")
        for q in reading
    )
    return {
        "id": row.id,
        "revision": row.revision,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "origin": "MANUAL" if row.source_type == "manual" else "USER_IMPORTED",
        "document": document,
        "practice_issues": practice_issues(parsed),
        "answer_key": {"trusted": trusted, "total": len(reading), "complete": trusted == len(reading)},
        "stats": stats
        or {"attempt_count": 0, "last_practiced": None, "latest_score": None, "best_score": None},
    }


async def practice_stats(db, user_id, question_ids):
    stats = {
        qid: {"attempt_count": 0, "last_practiced": None, "latest_score": None, "best_score": None}
        for qid in question_ids
    }
    for model in (ExamSession, SpeakingExamSession, ReadingExamSession):
        rows = await db.scalars(
            select(model).where(model.user_id == user_id, model.library_question_id.in_(question_ids))
        )
        for session in rows:
            info = stats[session.library_question_id]
            info["attempt_count"] += 1
            if isinstance(session, ReadingExamSession):
                score = session.result.score if session.result else None
            elif isinstance(session, SpeakingExamSession):
                score = session.grading.overall_score if session.grading else None
            else:
                attempts = session.attempts
                score = (
                    round(
                        sum(a.grading.overall_score * a.task_type for a in attempts)
                        / sum(a.task_type for a in attempts),
                        2,
                    )
                    if attempts and all(a.grading for a in attempts)
                    else None
                )
            if info["last_practiced"] is None or session.started_at > info["last_practiced"]:
                info["last_practiced"], info["latest_score"] = session.started_at, score
            if score is not None:
                info["best_score"] = (
                    max(info["best_score"], score) if info["best_score"] is not None else score
                )
    return stats
