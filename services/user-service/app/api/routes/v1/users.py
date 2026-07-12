from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import UserRepository
from app.schemas import (
    ExamTargetRequest,
    ExamTargetResponse,
    UserProfileUpdate,
    UserResponse,
)
from app.services import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    user = await service.get_user(user_id)
    response = UserResponse.model_validate(user)
    if user.profile:
        response.daily_study_hours_target = user.profile.daily_study_hours_target
        response.goal_type = user.profile.goal_type
    return response


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserProfileUpdate,
    service: UserService = Depends(get_user_service),
):
    user = await service.update_profile(user_id, data)
    response = UserResponse.model_validate(user)
    if user.profile:
        response.daily_study_hours_target = user.profile.daily_study_hours_target
        response.goal_type = user.profile.goal_type
    return response


@router.put("/{user_id}/exam-targets", response_model=ExamTargetResponse, status_code=201)
async def add_exam_target(
    user_id: int,
    data: ExamTargetRequest,
    service: UserService = Depends(get_user_service),
):
    return await service.add_exam_target(user_id, data)
