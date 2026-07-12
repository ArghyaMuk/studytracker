from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ExamTarget, User, UserProfile


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).options(selectinload(User.profile)).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.profile), selectinload(User.exam_targets))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def create_profile(self, profile: UserProfile) -> UserProfile:
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def get_exam_targets(self, user_id: int) -> list[ExamTarget]:
        result = await self.db.execute(
            select(ExamTarget).where(ExamTarget.user_id == user_id)
        )
        return list(result.scalars().all())

    async def add_exam_target(self, target: ExamTarget) -> ExamTarget:
        self.db.add(target)
        await self.db.commit()
        await self.db.refresh(target)
        return target
