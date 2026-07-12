import json
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import aio_pika

from .base import BaseEvent, EventType

logger = logging.getLogger(__name__)

EventHandler = Callable[[BaseEvent], Coroutine[Any, Any, None]]


class EventConsumer:
    """Consumes events from RabbitMQ with idempotency support."""

    def __init__(self, rabbitmq_url: str, service_name: str):
        self._rabbitmq_url = rabbitmq_url
        self._service_name = service_name
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._handlers: dict[EventType, EventHandler] = {}

    def on(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for an event type."""
        self._handlers[event_type] = handler

    async def start(self) -> None:
        """Start consuming events."""
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)

        exchange = await self._channel.declare_exchange(
            "studypilot.events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        for event_type in self._handlers:
            queue_name = f"{self._service_name}.{event_type.value}"
            queue = await self._channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=event_type.value)
            await queue.consume(self._process_message)
            logger.info(f"Consuming {event_type.value} on queue {queue_name}")

    async def _process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process(requeue=True):
            try:
                event = BaseEvent.model_validate_json(message.body)
                handler = self._handlers.get(event.event_type)
                if handler:
                    await handler(event)
                    logger.info(f"Processed event {event.event_id}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Message will be requeued on exception

    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
