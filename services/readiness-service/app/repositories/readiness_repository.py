from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReadinessScore


class ReadinessRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_subject_score(self, user_id: int, subject_code: str) -> ReadinessScore | None:
        result = await self.db.execute(
            select(ReadinessScore).where(
                ReadinessScore.user_id == user_id,
                ReadinessScore.subject_code == subject_code,
                ReadinessScore.unit_number.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_unit_scores(self, user_id: int, subject_code: str) -> list[ReadinessScore]:
        result = await self.db.execute(
            select(ReadinessScore).where(
                ReadinessScore.user_id == user_id,
                ReadinessScore.subject_code == subject_code,
                ReadinessScore.unit_number.isnot(None),
            )
        )
        return list(result.scalars().all())

    async def get_all_scores(self, user_id: int) -> list[ReadinessScore]:
        result = await self.db.execute(
            select(ReadinessScore).where(ReadinessScore.user_id == user_id)
        )
        return list(result.scalars().all())

    async def upsert_score(self, score: ReadinessScore) -> ReadinessScore:
        # Check if exists
        existing = await self.db.execute(
            select(ReadinessScore).where(
                ReadinessScore.user_id == score.user_id,
                ReadinessScore.subject_code == score.subject_code,
                ReadinessScore.unit_number == score.unit_number
                if score.unit_number
                else ReadinessScore.unit_number.is_(None),
            )
        )
        existing_score = existing.scalar_one_or_none()
        if existing_score:
            existing_score.score = score.score
            existing_score.breakdown_json = score.breakdown_json
            await self.db.commit()
            await self.db.refresh(existing_score)
            return existing_score
        else:
            self.db.add(score)
            await self.db.commit()
            await self.db.refresh(score)
            return score
