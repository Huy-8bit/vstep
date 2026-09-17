from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.llm.openai_client import OpenAILLMClient
from app.schemas.vocabulary_coach import (
    VocabularyRecommendationRequest,
    VocabularyReviewAnswer,
    VocabularyReviewCreate,
    VocabularySave,
    VocabularySourceSkill,
)
from app.services.vocabulary_coach_service import VocabularyCoachService, item_view, review_view

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary Coach"])


def coach(db):
    return VocabularyCoachService(db, OpenAILLMClient())


@router.post("/recommendations")
async def recommendations(
    data: VocabularyRecommendationRequest, db: DB, user: CurrentUser, generate: bool = True
):
    return await coach(db).recommend(data, user.id, generate)


@router.post("/items", status_code=201)
async def save(data: VocabularySave, db: DB, user: CurrentUser):
    return await coach(db).save(data, user.id)


@router.get("/items")
async def items(
    db: DB,
    user: CurrentUser,
    section: str = Query("DUE", pattern="^(DUE|NEW|LEARNING|MASTERED|ALL)$"),
    skill: VocabularySourceSkill | None = None,
    topic: str | None = None,
    search: str = Query("", max_length=100),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return await coach(db).list_items(user.id, section, skill, topic, offset, limit, search)


@router.get("/items/{item_id}")
async def item(item_id: str, db: DB, user: CurrentUser):
    return item_view(await coach(db).owned_item(item_id, user.id))


@router.get("/history")
async def history(
    db: DB, user: CurrentUser, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)
):
    return await coach(db).history(user.id, offset, limit)


@router.get("/progress")
async def progress(db: DB, user: CurrentUser):
    return await coach(db).progress(user.id)


@router.post("/reuse")
async def reuse(data: VocabularyRecommendationRequest, db: DB, user: CurrentUser):
    return await coach(db).reuse(data, user.id)


@router.post("/items/{item_id}/reviews", status_code=201)
async def create_review(item_id: str, data: VocabularyReviewCreate, db: DB, user: CurrentUser):
    return await coach(db).create_review(item_id, data, user.id)


@router.get("/reviews/{review_id}")
async def get_review(review_id: str, db: DB, user: CurrentUser):
    return review_view(await coach(db).owned_review(review_id, user.id))


@router.post("/reviews/{review_id}/answer")
async def answer_review(review_id: str, data: VocabularyReviewAnswer, db: DB, user: CurrentUser):
    return await coach(db).answer_review(review_id, data, user.id)
