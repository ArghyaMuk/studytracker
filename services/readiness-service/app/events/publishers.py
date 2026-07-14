"""Publishes readiness.updated events."""

from shared.events import EventPublisher, EventType


class ReadinessEventPublisher:
    def __init__(self, publisher: EventPublisher):
        self._publisher = publisher

    async def publish_readiness_updated(
        self,
        user_id: int,
        subject_code: str,
        unit_number: int | None,
        previous_score: float,
        new_score: float,
    ) -> str:
        from datetime import datetime, timezone

        return await self._publisher.publish(
            EventType.READINESS_UPDATED,
            payload={
                "user_id": user_id,
                "subject_code": subject_code,
                "unit_number": unit_number,
                "previous_score": previous_score,
                "new_score": new_score,
                "computation_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
