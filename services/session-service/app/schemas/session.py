from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=50)
    unit_number: int = Field(..., ge=1)
    duration_min: int = Field(..., ge=1, le=480)
    focus_rating: int = Field(..., ge=1, le=5)
    notes: str | None = Field(None, max_length=1000)


class SessionUpdate(BaseModel):
    duration_min: int | None = Field(None, ge=1, le=480)
    focus_rating: int | None = Field(None, ge=1, le=5)
    notes: str | None = Field(None, max_length=1000)


class SessionResponse(BaseModel):
    id: int
    user_id: int
    subject_code: str
    unit_number: int
    started_at: datetime | None
    duration_min: int
    focus_rating: int
    notes: str | None

    class Config:
        from_attributes = True
