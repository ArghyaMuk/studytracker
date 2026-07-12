"""Pluggable notification delivery interface.

Supports multiple channels: in-app, email, push.
New channels are added by implementing NotificationChannel.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    """Abstract interface for notification delivery."""

    @abstractmethod
    async def send(self, user_id: int, title: str, message: str) -> bool:
        """Send a notification. Returns True on success."""
        ...


class InAppChannel(NotificationChannel):
    """In-app notification delivery (writes to notification_log)."""

    async def send(self, user_id: int, title: str, message: str) -> bool:
        logger.info(f"[IN-APP] User {user_id}: {title} - {message}")
        return True


class EmailChannel(NotificationChannel):
    """Email notification delivery (SES/SendGrid placeholder)."""

    async def send(self, user_id: int, title: str, message: str) -> bool:
        # Placeholder — integrate SES/SendGrid here
        logger.info(f"[EMAIL] User {user_id}: {title}")
        return True
