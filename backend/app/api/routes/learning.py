from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy import select

from app.api.deps import DB, CurrentUser
from app.db.base import utcnow
from app.learning.analysis import PersonalizedLearningAnalysisService
from app.learning.coaching import PersonalizedCoachService
from app.learning.plans import StudyPlanService
from app.learning.signals import backfill_learning, profile_for
from app.learning.targeted import TargetedPracticeService
from app.llm.openai_client import OpenAILLMClient
from app.models.learning import PersonalizedExercise
from app.schemas.learning import (
    ExerciseSubmit,
    LearningSkill,
    PlanCreate,
    PlanItemUpdate,
    PracticeCreate,
    TargetPracticeCreate,
)
from app.services.entitlements import EntitlementService
from app.services.speech_transcription_service import speech_lock


async def require_learning(user: CurrentUser, db: DB):
    await EntitlementService(db).require(user, "LEARNING")


router = APIRouter(prefix="/learning", tags=["Personalized Learning"])


async def schedule_backfill(db, user_id, tasks, force=False):
    await speech_lock(db, f"learning:{user_id}")
    profile = await profile_for(db, user_id)
    stale = profile.backfill_status == "RUNNING" and profile.updated_at < utcnow() - timedelta(minutes=15)
    if profile.backfill_status == "PENDING" or stale or force and profile.backfill_status != "RUNNING":
        profile.backfill_status, profile.backfill_error = "RUNNING", None
        await db.commit()
        tasks.add_task(backfill_learning, user_id)
    return profile


@router.get("/overview")
async def overview(db: DB, user: CurrentUser, tasks: BackgroundTasks):
    if not (await EntitlementService(db).decision(user, "LEARNING")).allowed:
        return {"tier": "FREE", "message_vi": "Bạn cần thêm bài luyện để hệ thống phân tích điểm yếu. Nâng cấp VIP để xem bài học và kế hoạch chi tiết."}
    await schedule_backfill(db, user.id, tasks)
    return await PersonalizedLearningAnalysisService(db).overview(user.id)


@router.post("/recalculate", status_code=202, dependencies=[Depends(require_learning)])
async def recalculate(db: DB, user: CurrentUser, tasks: BackgroundTasks):
    profile = await schedule_backfill(db, user.id, tasks, force=True)
    return {"status": profile.backfill_status, "processed": profile.backfill_processed}


@router.get("/weaknesses", dependencies=[Depends(require_learning)])
async def weaknesses(
    db: DB,
    user: CurrentUser,
    skill: LearningSkill | None = None,
    category: str | None = Query(default=None, max_length=30),
    status: str | None = Query(default=None, max_length=20),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return await PersonalizedLearningAnalysisService(db).weaknesses(
        user.id, skill, category, status, limit, offset
    )


@router.get("/weaknesses/{identifier}", dependencies=[Depends(require_learning)])
async def detail(identifier: str, db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).detail(identifier, user.id)


@router.post("/weaknesses/{identifier}/lesson", dependencies=[Depends(require_learning)])
async def lesson(identifier: str, db: DB, user: CurrentUser):
    return await PersonalizedCoachService(db, OpenAILLMClient()).lesson(identifier, user.id)


@router.post("/weaknesses/{identifier}/practice", status_code=201, dependencies=[Depends(require_learning)])
async def practice(identifier: str, data: PracticeCreate, db: DB, user: CurrentUser):
    return await PersonalizedCoachService(db, OpenAILLMClient()).practice(identifier, user.id, data)


@router.post("/weaknesses/{identifier}/targeted-practice", status_code=201, dependencies=[Depends(require_learning)])
async def targeted(identifier: str, data: TargetPracticeCreate, db: DB, user: CurrentUser):
    return await TargetedPracticeService(db, OpenAILLMClient()).start(identifier, user.id, data)


@router.get("/exercises", dependencies=[Depends(require_learning)])
async def exercises(db: DB, user: CurrentUser):
    rows = await db.scalars(
        select(PersonalizedExercise)
        .where(PersonalizedExercise.user_id == user.id)
        .order_by(PersonalizedExercise.created_at.desc())
        .limit(20)
    )
    return {
        "items": [
            {
                "id": r.id,
                "title": r.content.get("title", "Luyện tập"),
                "weakness_id": r.weakness_id,
                "url": r.content.get("url") or f"/learning/practice?id={r.id}",
                "completed_at": r.completed_at,
                "created_at": r.created_at,
            }
            for r in rows
            if r.exercise_type != "TRANSFER" or r.content.get("url")
        ]
    }


@router.get("/exercises/{identifier}", dependencies=[Depends(require_learning)])
async def exercise(identifier: str, db: DB, user: CurrentUser):
    coach = PersonalizedCoachService(db, OpenAILLMClient())
    return await coach.exercise_view(await coach.owned_exercise(identifier, user.id), user.id)


@router.post("/exercises/{identifier}/answer", dependencies=[Depends(require_learning)])
async def answer(identifier: str, data: ExerciseSubmit, db: DB, user: CurrentUser):
    return await PersonalizedCoachService(db, OpenAILLMClient()).answer(identifier, user.id, data)


@router.get("/strengths", dependencies=[Depends(require_learning)])
async def strengths(db: DB, user: CurrentUser):
    return {"items": await PersonalizedLearningAnalysisService(db).strengths(user.id)}


@router.get("/attempts/{skill}/{attempt_id}", dependencies=[Depends(require_learning)])
async def attempt(
    skill: Literal["WRITING", "SPEAKING", "READING"], attempt_id: str, db: DB, user: CurrentUser
):
    return await PersonalizedLearningAnalysisService(db).attempt(user.id, skill, attempt_id)


@router.get("/today", dependencies=[Depends(require_learning)])
async def today(db: DB, user: CurrentUser):
    return await StudyPlanService(db).today(user.id)


@router.post("/study-plan", status_code=201, dependencies=[Depends(require_learning)])
async def create_plan(data: PlanCreate, db: DB, user: CurrentUser):
    return await StudyPlanService(db).create(user.id, data)


@router.get("/study-plan/current", dependencies=[Depends(require_learning)])
async def current_plan(db: DB, user: CurrentUser):
    return await StudyPlanService(db).current(user.id)


@router.patch("/study-plan/items/{identifier}", dependencies=[Depends(require_learning)])
async def update_plan_item(identifier: str, data: PlanItemUpdate, db: DB, user: CurrentUser):
    return await StudyPlanService(db).update_item(identifier, user.id, data)


@router.get("/writing", dependencies=[Depends(require_learning)])
async def writing(db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).skill(user.id, "WRITING")


@router.get("/speaking", dependencies=[Depends(require_learning)])
async def speaking(db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).skill(user.id, "SPEAKING")


@router.get("/reading", dependencies=[Depends(require_learning)])
async def reading(db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).skill(user.id, "READING")


@router.get("/grammar", dependencies=[Depends(require_learning)])
async def grammar(db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).weaknesses(user.id, category="GRAMMAR")


@router.get("/vocabulary", dependencies=[Depends(require_learning)])
async def vocabulary(db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).vocabulary(user.id)


@router.get("/weekly", dependencies=[Depends(require_learning)])
async def weekly(db: DB, user: CurrentUser):
    return await PersonalizedLearningAnalysisService(db).weekly(user.id)


@router.post("/weekly/summary", dependencies=[Depends(require_learning)])
async def weekly_summary(db: DB, user: CurrentUser):
    from app.learning.weekly import generate_summary

    return await generate_summary(db, OpenAILLMClient(), user.id)


@router.post("/vocabulary/reuses/{identifier}/answer", dependencies=[Depends(require_learning)])
async def verify_vocabulary_reuse(identifier: str, db: DB, user: CurrentUser):
    from app.learning.vocabulary import verify_reuse

    return await verify_reuse(db, OpenAILLMClient(), user.id, identifier)
