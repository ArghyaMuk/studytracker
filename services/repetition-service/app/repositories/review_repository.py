from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReviewItem


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(
        self, user_id: int, subject_code: str, unit_number: int
    ) -> ReviewItem:
        result = await self.db.execute(
            select(ReviewItem).where(
                ReviewItem.user_id == user_id,
                ReviewItem.subject_code == subject_code,
                ReviewItem.unit_number == unit_number,
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            item = ReviewItem(
                user_id=user_id,
                subject_code=subject_code,
                unit_number=unit_number,
                ease_factor=2.5,
                interval_days=1,
                repetitions=0,
                next_review_date=date.today(),
            )
            self.db.add(item)
            await self.db.commit()
            await self.db.refresh(item)
        return item

    async def update(self, item: ReviewItem) -> ReviewItem:
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_due_today(self, user_id: int) -> list[ReviewItem]:
        today = date.today()
        result = await self.db.execute(
            select(ReviewItem)
            .where(ReviewItem.user_id == user_id, ReviewItem.next_review_date <= today)
            .order_by(ReviewItem.next_review_date.asc())
            .limit(50)
        )
        return list(result.scalars().all())

    async def get_upcoming(self, user_id: int, days: int = 7) -> list[ReviewItem]:
        from datetime import timedelta

        end_date = date.today() + timedelta(days=days)
        result = await self.db.execute(
            select(ReviewItem)
            .where(
                ReviewItem.user_id == user_id,
                ReviewItem.next_review_date <= end_date,
            )
            .order_by(ReviewItem.next_review_date.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, item_id: int) -> ReviewItem | None:
        result = await self.db.execute(
            select(ReviewItem).where(ReviewItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_subject(self, user_id: int, subject_code: str) -> list[ReviewItem]:
        result = await self.db.execute(
            select(ReviewItem).where(
                ReviewItem.user_id == user_id,
                ReviewItem.subject_code == subject_code,
            )
        )
        return list(result.scalars().all())
