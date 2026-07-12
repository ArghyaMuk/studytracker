from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import NotificationPreference
from app.schemas import NotificationPreferenceRequest, NotificationPreferenceResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        # Return defaults
        return NotificationPreferenceResponse(
            user_id=user_id,
            daily_digest_enabled=True,
            readiness_alert_enabled=True,
            exam_countdown_enabled=True,
            inactivity_nudge_enabled=True,
            preferred_time="08:00",
        )
    return pref


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    data: NotificationPreferenceRequest,
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)

    pref.daily_digest_enabled = data.daily_digest_enabled
    pref.readiness_alert_enabled = data.readiness_alert_enabled
    pref.exam_countdown_enabled = data.exam_countdown_enabled
    pref.inactivity_nudge_enabled = data.inactivity_nudge_enabled
    pref.preferred_time = data.preferred_time

    await db.commit()
    await db.refresh(pref)
    return pref
