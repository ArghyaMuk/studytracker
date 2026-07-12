from datetime import date, datetime, timezone

from fastapi import HTTPException, status

from app.models import ReviewItem
from app.repositories import ReviewRepository
from .sm2_algorithm import compute_sm2


class RepetitionService:
    def __init__(self, repo: ReviewRepository):
        self.repo = repo

    async def grade_item(
        self, item_id: int, quality: int, exam_date: date | None = None, units_remaining: int | None = None
    ) -> ReviewItem:
        """Grade a review item with quality 0-5."""
        if quality < 0 or quality > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Quality must be between 0 and 5",
            )

        item = await self.repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found")

        result = compute_sm2(
            quality=quality,
            ease_factor=item.ease_factor,
            interval_days=item.interval_days,
            repetitions=item.repetitions,
            exam_date=exam_date,
            units_remaining=units_remaining,
        )

        item.ease_factor = result.ease_factor
        item.interval_days = result.interval_days
        item.repetitions = result.repetitions
        item.next_review_date = result.next_review_date
        item.last_reviewed_at = datetime.now(timezone.utc)

        return await self.repo.update(item)

    async def get_due_today(self, user_id: int) -> list[ReviewItem]:
        return await self.repo.get_due_today(user_id)

    async def get_upcoming(self, user_id: int, days: int = 7) -> list[ReviewItem]:
        return await self.repo.get_upcoming(user_id, days)

    async def handle_session_logged(
        self, user_id: int, subject_code: str, unit_number: int
    ) -> ReviewItem:
        """Handle a session.logged event by updating the review item."""
        item = await self.repo.get_or_create(user_id, subject_code, unit_number)

        # Treat session as a quality-3 recall (correct with difficulty)
        result = compute_sm2(
            quality=3,
            ease_factor=item.ease_factor,
            interval_days=item.interval_days,
            repetitions=item.repetitions,
        )

        item.ease_factor = result.ease_factor
        item.interval_days = result.interval_days
        item.repetitions = result.repetitions
        item.next_review_date = result.next_review_date
        item.last_reviewed_at = datetime.now(timezone.utc)

        return await self.repo.update(item)

    async def handle_quiz_completed(
        self, user_id: int, subject_code: str, unit_number: int, score_percentage: float
    ) -> ReviewItem:
        """Handle a quiz.completed event by mapping score to quality rating."""
        item = await self.repo.get_or_create(user_id, subject_code, unit_number)

        # Map percentage to quality: 0-20%->0, 20-40%->1, 40-60%->2, 60-75%->3, 75-90%->4, 90-100%->5
        if score_percentage >= 90:
            quality = 5
        elif score_percentage >= 75:
            quality = 4
        elif score_percentage >= 60:
            quality = 3
        elif score_percentage >= 40:
            quality = 2
        elif score_percentage >= 20:
            quality = 1
        else:
            quality = 0

        result = compute_sm2(
            quality=quality,
            ease_factor=item.ease_factor,
            interval_days=item.interval_days,
            repetitions=item.repetitions,
        )

        item.ease_factor = result.ease_factor
        item.interval_days = result.interval_days
        item.repetitions = result.repetitions
        item.next_review_date = result.next_review_date
        item.last_reviewed_at = datetime.now(timezone.utc)

        return await self.repo.update(item)
