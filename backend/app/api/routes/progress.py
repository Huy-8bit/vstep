from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])


@router.get("/summary")
async def summary(db: DB, user: CurrentUser):
    return await ProgressService(db).summary(user.id)


@router.get("/errors")
async def errors(db: DB, user: CurrentUser):
    return await ProgressService(db).errors(user.id)
