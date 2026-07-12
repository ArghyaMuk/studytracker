from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StudySession


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, session: StudySession) -> StudySession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, session_id: int) -> StudySession | None:
        result = await self.db.execute(
            select(StudySession).where(
                StudySession.id == session_id, StudySession.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_sessions(
        self,
        user_id: int,
        subject_code: str | None = None,
        unit_number: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StudySession]:
        query = select(StudySession).where(
            StudySession.user_id == user_id, StudySession.is_deleted == False
        )
        if subject_code:
            query = query.where(StudySession.subject_code == subject_code)
        if unit_number:
            query = query.where(StudySession.unit_number == unit_number)

        query = query.order_by(StudySession.started_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, session: StudySession) -> None:
        session.is_deleted = True
        await self.db.commit()

    async def update(self, session: StudySession) -> StudySession:
        await self.db.commit()
        await self.db.refresh(session)
        return session
