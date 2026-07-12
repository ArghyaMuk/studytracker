import logging

from app.models import ReadinessScore
from app.repositories import ReadinessRepository
from .score_calculator import ReadinessCalculator, SignalData

logger = logging.getLogger(__name__)


class ReadinessService:
    def __init__(self, repo: ReadinessRepository):
        self.repo = repo
        self.calculator = ReadinessCalculator()

    async def get_subject_readiness(self, user_id: int, subject_code: str) -> dict:
        """Get subject-level and unit-level readiness scores."""
        subject_score = await self.repo.get_subject_score(user_id, subject_code)
        unit_scores = await self.repo.get_unit_scores(user_id, subject_code)

        return {
            "subject_code": subject_code,
            "overall_score": subject_score.score if subject_score else 0.0,
            "unit_scores": unit_scores,
        }

    async def get_all_readiness(self, user_id: int) -> list[ReadinessScore]:
        """Get all readiness scores for a user."""
        return await self.repo.get_all_scores(user_id)

    async def recompute_score(
        self,
        user_id: int,
        subject_code: str,
        unit_number: int | None,
        signals: SignalData,
        goal_type: str = "semester_exam",
    ) -> ReadinessScore:
        """Recompute and persist a readiness score."""
        score_value, breakdown = self.calculator.compute(signals, goal_type)

        readiness = ReadinessScore(
            user_id=user_id,
            subject_code=subject_code,
            unit_number=unit_number,
            score=score_value,
            breakdown_json=breakdown,
        )
        return await self.repo.upsert_score(readiness)
