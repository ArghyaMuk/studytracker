import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    SESSION_LOGGED = "session.logged"
    SESSION_DELETED = "session.deleted"
    QUIZ_COMPLETED = "quiz.completed"
    READINESS_UPDATED = "readiness.updated"


class BaseEvent(BaseModel):
    """Base event schema for all inter-service events."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    payload: dict[str, Any]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
