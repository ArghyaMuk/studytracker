from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import UserRepository
from app.schemas import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.services import UserService
from shared.auth import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegisterRequest, service: UserService = Depends(get_user_service)):
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, service: UserService = Depends(get_user_service)):
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest, service: UserService = Depends(get_user_service)):
    return await service.refresh_token(data)


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password for a user by email."""
    repo = UserRepository(db)
    user = await repo.get_by_email(data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No account found with this email")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 8 characters")

    user.password_hash = hash_password(data.new_password)
    await db.commit()
    return {"message": "Password reset successfully"}
