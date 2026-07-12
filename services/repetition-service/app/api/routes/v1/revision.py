from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import ReviewRepository
from app.schemas import GradeRequest, ReviewItemResponse
from app.services import RepetitionService

router = APIRouter(prefix="/revision", tags=["revision"])


def get_repetition_service(db: AsyncSession = Depends(get_db)) -> RepetitionService:
    return RepetitionService(ReviewRepository(db))


@router.get("/today", response_model=list[ReviewItemResponse])
async def get_today_revision(
    user_id: int = Query(...),
    service: RepetitionService = Depends(get_repetition_service),
):
    return await service.get_due_today(user_id)


@router.get("/upcoming", response_model=list[ReviewItemResponse])
async def get_upcoming_revision(
    user_id: int = Query(...),
    days: int = Query(7, ge=1, le=30),
    service: RepetitionService = Depends(get_repetition_service),
):
    return await service.get_upcoming(user_id, days)


@router.post("/{item_id}/grade", response_model=ReviewItemResponse)
async def grade_item(
    item_id: int,
    data: GradeRequest,
    service: RepetitionService = Depends(get_repetition_service),
):
    return await service.grade_item(item_id, data.quality)
