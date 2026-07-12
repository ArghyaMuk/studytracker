from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import ReadinessRepository
from app.schemas import ReadinessScoreResponse, SubjectReadinessResponse
from app.services import ReadinessService

router = APIRouter(prefix="/readiness", tags=["readiness"])


def get_readiness_service(db: AsyncSession = Depends(get_db)) -> ReadinessService:
    return ReadinessService(ReadinessRepository(db))


@router.get("/{user_id}/{subject_code}", response_model=SubjectReadinessResponse)
async def get_subject_readiness(
    user_id: int,
    subject_code: str,
    service: ReadinessService = Depends(get_readiness_service),
):
    return await service.get_subject_readiness(user_id, subject_code)


@router.get("/{user_id}", response_model=list[ReadinessScoreResponse])
async def get_all_readiness(
    user_id: int, service: ReadinessService = Depends(get_readiness_service)
):
    return await service.get_all_readiness(user_id)
