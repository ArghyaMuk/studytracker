"""Event consumers for the Readiness Service.

Consumes: session.logged, quiz.completed
Triggers readiness score recomputation.
"""

import logging

from shared.events import BaseEvent, EventConsumer, EventType

from app.core.db import async_session_factory
from app.repositories import ReadinessRepository
from app.services import ReadinessService
from app.services.score_calculator import SignalData

logger = logging.getLogger(__name__)


async def handle_session_logged(event: BaseEvent) -> None:
    """Recompute readiness on session logged."""
    payload = event.payload
    async with async_session_factory() as db:
        service = ReadinessService(ReadinessRepository(db))
        # Simplified recompute — in production, gather all signals from other services
        signals = SignalData(consistency=70.0)  # Placeholder
        await service.recompute_score(
            user_id=payload["user_id"],
            subject_code=payload["subject_code"],
            unit_number=payload["unit_number"],
            signals=signals,
        )
    logger.info(f"Recomputed readiness for user {payload['user_id']}")


async def handle_quiz_completed(event: BaseEvent) -> None:
    """Recompute readiness on quiz completed."""
    payload = event.payload
    async with async_session_factory() as db:
        service = ReadinessService(ReadinessRepository(db))
        signals = SignalData(quiz_accuracy=payload.get("score_percentage", 0))
        await service.recompute_score(
            user_id=payload["user_id"],
            subject_code=payload["subject_code"],
            unit_number=payload.get("unit_number"),
            signals=signals,
        )
    logger.info(f"Recomputed readiness from quiz for user {payload['user_id']}")


def register_consumers(consumer: EventConsumer) -> None:
    consumer.on(EventType.SESSION_LOGGED, handle_session_logged)
    consumer.on(EventType.QUIZ_COMPLETED, handle_quiz_completed)
