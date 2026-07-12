from datetime import datetime

from pydantic import BaseModel, Field


class QuizGenerateRequest(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=50)
    unit_number: int | None = None
    notes_text: str | None = None
    pyq_upload_id: int | None = None
    difficulty: str = Field("medium", pattern="^(easy|medium|hard)$")
    count: int = Field(10, ge=1, le=50)
    mode: str = Field("mcq", pattern="^(mcq|viva)$")


class QuestionResponse(BaseModel):
    id: int
    question: str
    options_json: str | None
    difficulty: str
    source_pyq_year: int | None

    class Config:
        from_attributes = True


class QuizResponse(BaseModel):
    id: int
    user_id: int
    subject_code: str
    unit_number: int | None
    source_type: str
    mode: str
    created_at: datetime | None
    questions: list[QuestionResponse] = []

    class Config:
        from_attributes = True


class QuizSubmitRequest(BaseModel):
    answers: dict[int, str]  # question_id -> selected_answer


class QuizSubmitResponse(BaseModel):
    quiz_id: int
    score: float
    total_questions: int
    correct_count: int
    feedback: list[dict]  # per-question feedback


class PYQUploadResponse(BaseModel):
    id: int
    subject_code: str
    year: int
    parsed_status: str

    class Config:
        from_attributes = True
