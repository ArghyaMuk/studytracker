"""
Event Consumer – Subscribes to domain events from RabbitMQ.

Each service registers handlers for the event types it cares about. The consumer
creates a dedicated durable queue per (service, event_type) pair, binds it to the
shared topic exchange, and dispatches incoming messages to the registered handler.

Idempotency: messages are auto-acknowledged only after successful processing.
On failure, messages are requeued (requeue=True) so they can be retried later.
"""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

import aio_pika

from .base import BaseEvent, EventType

logger = logging.getLogger(__name__)

# Type alias for async event handler functions
EventHandler = Callable[[BaseEvent], Coroutine[Any, Any, None]]


class EventConsumer:
    """Consumes events from RabbitMQ with at-least-once delivery guarantees."""

    def __init__(self, rabbitmq_url: str, service_name: str):
        self._rabbitmq_url = rabbitmq_url
        self._service_name = service_name  # Used to namespace queue names
        self._connection: aio_pika.abc.AbstractConnection | None = None
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._handlers: dict[EventType, EventHandler] = {}

    def on(self, event_type: EventType, handler: EventHandler) -> None:
        """Register an async handler for a specific event type."""
        self._handlers[event_type] = handler

    async def start(self) -> None:
        """Connect to RabbitMQ and begin consuming registered event types.

        For each registered handler:
        - Declares a durable queue named '{service}.{event_type}'
        - Binds it to the topic exchange with the event type as routing key
        - Starts consuming with prefetch=10 for throughput
        """
        self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        self._channel = await self._connection.channel()
        # Prefetch limits how many unacked messages this consumer holds at once
        await self._channel.set_qos(prefetch_count=10)

        exchange = await self._channel.declare_exchange(
            "studypilot.events", aio_pika.ExchangeType.TOPIC, durable=True
        )

        # Create a queue + binding for each event type we want to handle
        for event_type in self._handlers:
            # Queue name is scoped to the service to avoid cross-service conflicts
            queue_name = f"{self._service_name}.{event_type.value}"
            queue = await self._channel.declare_queue(queue_name, durable=True)
            await queue.bind(exchange, routing_key=event_type.value)
            await queue.consume(self._process_message)
            logger.info(f"Consuming {event_type.value} on queue {queue_name}")

    async def _process_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """Deserialize and dispatch a single message to its handler.

        Uses message.process(requeue=True) context manager:
        - On success: message is acknowledged and removed from the queue.
        - On exception: message is requeued for retry (at-least-once semantics).
        Handlers should be idempotent since redelivery is possible.
        """
        async with message.process(requeue=True):
            try:
                # Parse the raw message body into a validated event model
                event = BaseEvent.model_validate_json(message.body)
                handler = self._handlers.get(event.event_type)
                if handler:
                    await handler(event)
                    logger.info(f"Processed event {event.event_id}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # Exception propagates → message.process() requeues the message

    async def close(self) -> None:
        """Gracefully close the RabbitMQ connection."""
        if self._connection:
            await self._connection.close()
