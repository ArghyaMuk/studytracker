from datetime import datetime

from pydantic import BaseModel


class ReadinessScoreResponse(BaseModel):
    subject_code: str
    unit_number: int | None
    score: float
    computed_at: datetime | None
    breakdown_json: str | None

    class Config:
        from_attributes = True


class SubjectReadinessResponse(BaseModel):
    subject_code: str
    overall_score: float
    unit_scores: list[ReadinessScoreResponse]
