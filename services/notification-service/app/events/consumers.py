"""Event consumers for the Notification Service.

Consumes: readiness.updated
"""

import logging

from shared.events import BaseEvent, EventConsumer, EventType

logger = logging.getLogger(__name__)


async def handle_readiness_updated(event: BaseEvent) -> None:
    """Handle readiness.updated event — notify user of readiness change."""
    payload = event.payload
    logger.info(
        f"Received readiness.updated for user {payload.get('user_id')} "
        f"subject={payload.get('subject_code')} unit={payload.get('unit_number')} "
        f"score={payload.get('score')}"
    )
    # TODO: Implement actual notification delivery (email, push, in-app)


def register_consumers(consumer: EventConsumer) -> None:
    """Register all event handlers."""
    consumer.on(EventType.READINESS_UPDATED, handle_readiness_updated)
