import logging

from fastapi import HTTPException, status

from app.clients import CurriculumClient
from app.events import SessionEventPublisher
from app.models import StudySession
from app.repositories import SessionRepository
from app.schemas import SessionCreate, SessionUpdate

logger = logging.getLogger(__name__)


class SessionService:
    def __init__(
        self,
        repo: SessionRepository,
        curriculum_client: CurriculumClient,
        event_publisher: SessionEventPublisher | None = None,
    ):
        self.repo = repo
        self.curriculum_client = curriculum_client
        self.event_publisher = event_publisher

    async def create_session(self, user_id: int, data: SessionCreate) -> StudySession:
        # Validate subject/unit against Curriculum Service
        try:
            is_valid = await self.curriculum_client.validate_subject_unit(
                data.subject_code, data.unit_number
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid subject code '{data.subject_code}' or unit number {data.unit_number}",
                )
        except RuntimeError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Curriculum validation could not be completed",
            )

        session = StudySession(
            user_id=user_id,
            subject_code=data.subject_code,
            unit_number=data.unit_number,
            duration_min=data.duration_min,
            focus_rating=data.focus_rating,
            notes=data.notes,
        )
        session = await self.repo.create(session)

        # Publish event (best-effort)
        if self.event_publisher:
            try:
                await self.event_publisher.publish_session_logged(
                    user_id=user_id,
                    subject_code=data.subject_code,
                    unit_number=data.unit_number,
                    duration_minutes=data.duration_min,
                    focus_rating=data.focus_rating,
                    session_timestamp=session.started_at.isoformat() if session.started_at else "",
                )
            except Exception as e:
                logger.warning(f"Failed to publish session.logged event: {e}")

        return session

    async def get_session(self, session_id: int) -> StudySession:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    async def get_sessions(
        self,
        user_id: int,
        subject_code: str | None = None,
        unit_number: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StudySession]:
        return await self.repo.get_sessions(user_id, subject_code, unit_number, limit, offset)

    async def update_session(self, session_id: int, data: SessionUpdate) -> StudySession:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        update_data = data.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(session, key, value)
        return await self.repo.update(session)

    async def delete_session(self, session_id: int) -> None:
        session = await self.repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        await self.repo.soft_delete(session)

        if self.event_publisher:
            try:
                await self.event_publisher.publish_session_deleted(
                    user_id=session.user_id,
                    subject_code=session.subject_code,
                    unit_number=session.unit_number,
                    session_id=session.id,
                )
            except Exception as e:
                logger.warning(f"Failed to publish session.deleted event: {e}")
