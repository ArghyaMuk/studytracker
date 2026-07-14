from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import User, UserProfile
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


@router.get("/admin/all")
async def list_all_users(
    x_user_role: str = Header("student", alias="X-User-Role"),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint: list all registered users with stats."""
    if x_user_role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    result = await db.execute(
        select(User.id, User.name, User.email, User.college, User.current_semester, User.created_at)
        .order_by(User.created_at.desc())
    )
    users = [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "college": row.college,
            "current_semester": row.current_semester,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in result.all()
    ]

    # Stats
    count_result = await db.execute(select(func.count(User.id)))
    total_users = count_result.scalar()

    return {
        "total_users": total_users,
        "users": users,
    }


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
