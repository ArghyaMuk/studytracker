"""
Event Publisher – Publishes domain events to RabbitMQ.

Uses a durable topic exchange ('studypilot.events') so that multiple consumers
can bind queues with routing-key patterns and receive only the events they
care about. Messages are persisted to disk (PERSISTENT delivery mode) to
survive broker restarts.
"""

import logging
from typing import Any

import aio_pika

from .base import BaseEvent, EventType

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes events to RabbitMQ with schema validation."""

    def __init__(self, rabbitmq_url: str):
        self._rabbitmq_url = rabbitmq_url
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self) -> None:
        """Establish connection and declare the shared topic exchange.

        Uses connect_robust for automatic reconnection on transient failures.
        """
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        # Declare (or verify) the durable topic exchange shared by all services
        await self._channel.declare_exchange(
            "studypilot.events", aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> str:
        """Publish a domain event. Returns the generated event_id.

        Lazy-connects if called before an explicit connect() – ensures the
        publisher is always ready to send.
        """
        if not self._channel:
            await self.connect()

        # Build a validated event envelope with unique ID and timestamp
        event = BaseEvent(
            event_type=event_type,
            payload=payload,
            **({"correlation_id": correlation_id} if correlation_id else {}),
        )

        exchange = await self._channel.get_exchange("studypilot.events")

        # Construct the AMQP message with persistence and content metadata
        message = aio_pika.Message(
            body=event.model_dump_json().encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # Survives broker restarts
            message_id=event.event_id,  # Allows consumers to deduplicate
        )

        # Route using event_type as the topic key (e.g. "session.completed")
        await exchange.publish(message, routing_key=event_type.value)
        logger.info(f"Published event {event.event_id} type={event_type.value}")
        return event.event_id

    async def close(self) -> None:
        """Gracefully close the RabbitMQ connection."""
        if self._connection:
            await self._connection.close()
