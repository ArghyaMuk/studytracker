from shared.events import EventPublisher, EventType


class SessionEventPublisher:
    """Publishes session domain events."""

    def __init__(self, publisher: EventPublisher):
        self._publisher = publisher

    async def publish_session_logged(
        self,
        user_id: int,
        subject_code: str,
        unit_number: int,
        duration_minutes: int,
        focus_rating: int,
        session_timestamp: str,
    ) -> str:
        return await self._publisher.publish(
            EventType.SESSION_LOGGED,
            payload={
                "user_id": user_id,
                "subject_code": subject_code,
                "unit_number": unit_number,
                "duration_minutes": duration_minutes,
                "focus_rating": focus_rating,
                "session_timestamp": session_timestamp,
            },
        )

    async def publish_session_deleted(
        self, user_id: int, subject_code: str, unit_number: int, session_id: int
    ) -> str:
        return await self._publisher.publish(
            EventType.SESSION_DELETED,
            payload={
                "user_id": user_id,
                "subject_code": subject_code,
                "unit_number": unit_number,
                "session_id": session_id,
            },
        )
