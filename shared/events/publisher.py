import json
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
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        # Declare the exchange
        await self._channel.declare_exchange(
            "studypilot.events", aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def publish(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> str:
        """Publish an event. Returns the event_id."""
        if not self._channel:
            await self.connect()

        event = BaseEvent(
            event_type=event_type,
            payload=payload,
            **({"correlation_id": correlation_id} if correlation_id else {}),
        )

        exchange = await self._channel.get_exchange("studypilot.events")
        message = aio_pika.Message(
            body=event.model_dump_json().encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=event.event_id,
        )

        await exchange.publish(message, routing_key=event_type.value)
        logger.info(f"Published event {event.event_id} type={event_type.value}")
        return event.event_id

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
