from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import CurriculumClient
from app.core.db import get_db
from app.repositories import SessionRepository
from app.schemas import SessionCreate, SessionResponse, SessionUpdate
from app.services import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(
        repo=SessionRepository(db),
        curriculum_client=CurriculumClient(),
        event_publisher=None,  # Injected at app startup when RabbitMQ is configured
    )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    data: SessionCreate,
    user_id: int = Query(..., description="User ID"),
    service: SessionService = Depends(get_session_service),
):
    return await service.create_session(user_id, data)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    user_id: int = Query(...),
    subject_code: str | None = Query(None),
    unit_number: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SessionService = Depends(get_session_service),
):
    return await service.get_sessions(user_id, subject_code, unit_number, limit, offset)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, service: SessionService = Depends(get_session_service)):
    return await service.get_session(session_id)


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    data: SessionUpdate,
    service: SessionService = Depends(get_session_service),
):
    return await service.update_session(session_id, data)


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: int, service: SessionService = Depends(get_session_service)):
    await service.delete_session(session_id)
