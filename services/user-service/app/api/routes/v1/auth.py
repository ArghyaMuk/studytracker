from fastapi import APIRouter, Depends
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

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegisterRequest, service: UserService = Depends(get_user_service)):
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLoginRequest, service: UserService = Depends(get_user_service)):
    return await service.login(data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: TokenRefreshRequest, service: UserService = Depends(get_user_service)):
    return await service.refresh_token(data)
