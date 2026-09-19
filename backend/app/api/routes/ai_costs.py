from fastapi import APIRouter, Query
from pydantic import Field
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.common.errors import AppError
from app.models import WritingAttempt, WritingCalibrationSample
from app.models.evaluation import GradingModelEvaluation
from app.schemas.writing import StrictModel
from app.services.ai_cost_service import AICostService, require_cost_admin

router = APIRouter(prefix="/internal/ai-costs", tags=["AI Operations"])


@router.get("")
async def costs(db: DB, user: CurrentUser, days: int = Query(default=1, ge=1, le=90)):
    require_cost_admin(user)
    return await AICostService(db).overview(days)


@router.get("/attempts/{identifier}")
async def attempt_cost(identifier: str, db: DB, user: CurrentUser):
    require_cost_admin(user)
    return await AICostService(db).attempt(identifier)


@router.get("/evaluations")
async def evaluations(db: DB, user: CurrentUser):
    require_cost_admin(user)
    rows = await db.scalars(
        select(GradingModelEvaluation).order_by(GradingModelEvaluation.created_at.desc()).limit(50)
    )
    return {
        "items": [
            {
                "id": r.id,
                "model": r.model,
                "reasoning_effort": r.reasoning_effort,
                "dataset_version": r.dataset_version,
                "sample_count": r.sample_count,
                "metrics": r.metrics,
                "versions": r.versions,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


class TeacherReference(StrictModel):
    task_fulfillment: float = Field(ge=0, le=10, multiple_of=0.5)
    organization: float = Field(ge=0, le=10, multiple_of=0.5)
    vocabulary: float = Field(ge=0, le=10, multiple_of=0.5)
    grammar: float = Field(ge=0, le=10, multiple_of=0.5)
    overall: float = Field(ge=0, le=10)
    notes: str = Field(min_length=10, max_length=3000)


@router.post("/human-references/{attempt_id}", status_code=201)
async def teacher_reference(attempt_id: str, data: TeacherReference, db: DB, user: CurrentUser):
    require_cost_admin(user)
    a = await db.get(WritingAttempt, attempt_id)
    if not a or not a.grading:
        raise AppError(404, "Không tìm thấy bài đã chấm.")
    q = a.question
    sample = WritingCalibrationSample(
        question_id=q.id,
        task_type=a.task_type,
        question="\n\n".join(filter(None, [q.instruction, q.stimulus, q.response_instruction])),
        answer=a.answer,
        human_task_score=data.task_fulfillment,
        human_organization_score=data.organization,
        human_vocabulary_score=data.vocabulary,
        human_grammar_score=data.grammar,
        human_overall_score=data.overall,
        reviewer_count=1,
        notes=f"Human reviewer user_id={user.id}; source_attempt_id={a.id}\n{data.notes}",
    )
    db.add(sample)
    await db.commit()
    return {"id": sample.id, "source": "human_reviewed", "ai_score_preserved": True}
