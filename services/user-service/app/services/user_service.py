from fastapi import HTTPException, status
from shared.auth import hash_password, verify_password

from app.core.security import create_tokens, decode_token
from app.models import ExamTarget, User, UserProfile
from app.repositories import UserRepository
from app.schemas import (
    ExamTargetRequest,
    TokenRefreshRequest,
    UserLoginRequest,
    UserProfileUpdate,
    UserRegisterRequest,
)


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserRegisterRequest) -> dict:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        user = User(
            name=data.name,
            email=data.email,
            password_hash=hash_password(data.password),
            college=data.college,
            university=data.university,
            program_id=data.program_id,
            current_semester=data.current_semester,
        )
        user = await self.repo.create(user)

        # Create default profile
        profile = UserProfile(
            user_id=user.id,
            daily_study_hours_target=2.0,
            goal_type="semester_exam",
        )
        await self.repo.create_profile(profile)

        return create_tokens(user.id, user.email, user.role or "student")

    async def login(self, data: UserLoginRequest) -> dict:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return create_tokens(user.id, user.email, user.role or "student")

    async def refresh_token(self, data: TokenRefreshRequest) -> dict:
        payload = decode_token(data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        user_id = int(payload["sub"])
        email = payload["email"]
        role = payload.get("role", "student")
        return create_tokens(user_id, email, role)

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def update_profile(self, user_id: int, data: UserProfileUpdate) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update user fields
        update_data = data.model_dump(exclude_none=True)
        profile_fields = {"daily_study_hours_target", "goal_type"}

        for key, value in update_data.items():
            if key in profile_fields:
                if user.profile:
                    setattr(user.profile, key, value)
            else:
                setattr(user, key, value)

        return await self.repo.update(user)

    async def add_exam_target(self, user_id: int, data: ExamTargetRequest) -> ExamTarget:
        target = ExamTarget(
            user_id=user_id,
            subject_code=data.subject_code,
            exam_type=data.exam_type,
            exam_date=data.exam_date,
        )
        return await self.repo.add_exam_target(target)
