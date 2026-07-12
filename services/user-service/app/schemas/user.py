import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    college: str = Field(None, max_length=200)
    university: str = Field(None, max_length=200)
    program_id: int | None = None
    current_semester: int | None = Field(None, ge=1, le=12)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserProfileUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    college: str | None = Field(None, max_length=200)
    university: str | None = Field(None, max_length=200)
    program_id: int | None = None
    current_semester: int | None = Field(None, ge=1, le=12)
    daily_study_hours_target: float | None = Field(None, ge=0.5, le=16.0)
    goal_type: str | None = None

    @field_validator("goal_type")
    @classmethod
    def validate_goal_type(cls, v: str | None) -> str | None:
        if v and v not in ("semester_exam", "placement_prep", "competitive_exam"):
            raise ValueError("goal_type must be one of: semester_exam, placement_prep, competitive_exam")
        return v


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    college: str | None
    university: str | None
    program_id: int | None
    current_semester: int | None
    daily_study_hours_target: float | None = None
    goal_type: str | None = None

    class Config:
        from_attributes = True


class ExamTargetRequest(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=50)
    exam_type: str
    exam_date: datetime

    @field_validator("exam_type")
    @classmethod
    def validate_exam_type(cls, v: str) -> str:
        if v not in ("internal", "external"):
            raise ValueError("exam_type must be 'internal' or 'external'")
        return v


class ExamTargetResponse(BaseModel):
    id: int
    subject_code: str
    exam_type: str
    exam_date: datetime

    class Config:
        from_attributes = True
