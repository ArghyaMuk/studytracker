from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request as FastAPIRequest, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import CurriculumClient
from app.core.db import get_db
from app.repositories import SessionRepository
from app.schemas import SessionCreate, SessionResponse, SessionUpdate
from app.services import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


async def get_current_user_id(x_user_id: str = Header(None, alias="X-User-Id")) -> int:
    """Extract authenticated user from gateway header."""
    if not x_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return int(x_user_id)


def get_session_service(db: AsyncSession = Depends(get_db)) -> SessionService:
    return SessionService(
        repo=SessionRepository(db),
        curriculum_client=CurriculumClient(),
        event_publisher=None,
    )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    request: FastAPIRequest,
    data: SessionCreate,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    publisher = getattr(request.app.state, "event_publisher", None)
    service = SessionService(
        repo=SessionRepository(db),
        curriculum_client=CurriculumClient(),
        event_publisher=publisher,
    )
    return await service.create_session(current_user, data)


@router.get("", response_model=list[SessionResponse])
async def list_sessions(
    current_user: int = Depends(get_current_user_id),
    user_id: int = Query(None),
    subject_code: str | None = Query(None),
    unit_number: int | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SessionService = Depends(get_session_service),
):
    # Users can only query their own sessions
    target_user = user_id if user_id else current_user
    if target_user != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access other user's sessions")
    return await service.get_sessions(current_user, subject_code, unit_number, limit, offset)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    session_obj = await service.get_session(session_id)
    if session_obj.user_id != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return session_obj


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    data: SessionUpdate,
    current_user: int = Depends(get_current_user_id),
    service: SessionService = Depends(get_session_service),
):
    session_obj = await service.get_session(session_id)
    if session_obj.user_id != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    return await service.update_session(session_id, data)


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    request: FastAPIRequest,
    session_id: int,
    current_user: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    publisher = getattr(request.app.state, "event_publisher", None)
    service = SessionService(
        repo=SessionRepository(db),
        curriculum_client=CurriculumClient(),
        event_publisher=publisher,
    )
    session_obj = await service.get_session(session_id)
    if session_obj.user_id != current_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your session")
    await service.delete_session(session_id)
