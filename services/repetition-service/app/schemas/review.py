from datetime import date, datetime

from pydantic import BaseModel, Field


class GradeRequest(BaseModel):
    quality: int = Field(..., ge=0, le=5, description="Recall quality 0-5")


class ReviewItemResponse(BaseModel):
    id: int
    user_id: int
    subject_code: str
    unit_number: int
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: date
    last_reviewed_at: datetime | None

    class Config:
        from_attributes = True
