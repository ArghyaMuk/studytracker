from pydantic import BaseModel, Field


class NotificationPreferenceRequest(BaseModel):
    daily_digest_enabled: bool = True
    readiness_alert_enabled: bool = True
    exam_countdown_enabled: bool = True
    inactivity_nudge_enabled: bool = True
    preferred_time: str = Field("08:00", pattern=r"^\d{2}:\d{2}$")


class NotificationPreferenceResponse(BaseModel):
    user_id: int
    daily_digest_enabled: bool
    readiness_alert_enabled: bool
    exam_countdown_enabled: bool
    inactivity_nudge_enabled: bool
    preferred_time: str

    class Config:
        from_attributes = True
