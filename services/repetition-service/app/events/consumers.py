"""Event consumers for the Spaced Repetition Service.

Consumes: session.logged, quiz.completed
"""

import logging

from shared.events import BaseEvent, EventConsumer, EventType

from app.core.db import async_session_factory
from app.repositories import ReviewRepository
from app.services import RepetitionService

logger = logging.getLogger(__name__)


async def handle_session_logged(event: BaseEvent) -> None:
    """Handle session.logged event — update review item."""
    payload = event.payload
    async with async_session_factory() as db:
        service = RepetitionService(ReviewRepository(db))
        await service.handle_session_logged(
            user_id=payload["user_id"],
            subject_code=payload["subject_code"],
            unit_number=payload["unit_number"],
        )
    logger.info(f"Processed session.logged for user {payload['user_id']}")


async def handle_quiz_completed(event: BaseEvent) -> None:
    """Handle quiz.completed event — update review item based on score."""
    payload = event.payload
    async with async_session_factory() as db:
        service = RepetitionService(ReviewRepository(db))
        await service.handle_quiz_completed(
            user_id=payload["user_id"],
            subject_code=payload["subject_code"],
            unit_number=payload["unit_number"],
            score_percentage=payload["score_percentage"],
        )
    logger.info(f"Processed quiz.completed for user {payload['user_id']}")


def register_consumers(consumer: EventConsumer) -> None:
    """Register all event handlers."""
    consumer.on(EventType.SESSION_LOGGED, handle_session_logged)
    consumer.on(EventType.QUIZ_COMPLETED, handle_quiz_completed)
