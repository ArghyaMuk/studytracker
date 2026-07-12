import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Quiz, QuizQuestion
from app.repositories import QuizRepository

router = APIRouter(prefix="/admin/quizzes", tags=["admin-quizzes"])


class CustomQuestionInput(BaseModel):
    question: str
    options_json: str | None = None
    correct_answer: str
    difficulty: str = "medium"


class CustomQuizRequest(BaseModel):
    subject_code: str = Field(..., min_length=1, max_length=50)
    unit_number: int = Field(..., ge=1)
    mode: str = Field("mcq", pattern="^(mcq|viva)$")
    questions: list[CustomQuestionInput] = Field(..., min_length=1, max_length=50)


class CustomQuizResponse(BaseModel):
    id: int
    subject_code: str
    unit_number: int
    mode: str
    question_count: int


@router.post("/custom", response_model=CustomQuizResponse, status_code=201)
async def create_custom_quiz(data: CustomQuizRequest, db: AsyncSession = Depends(get_db)):
    """Admin endpoint to create a quiz with manually written questions."""
    repo = QuizRepository(db)

    # Create quiz record
    quiz = Quiz(
        user_id=0,  # Admin-created, no specific user
        subject_code=data.subject_code,
        unit_number=data.unit_number,
        source_type="unit",
        mode=data.mode,
    )
    quiz = await repo.create_quiz(quiz)

    # Add questions
    questions = []
    for q in data.questions:
        question = QuizQuestion(
            quiz_id=quiz.id,
            question=q.question,
            options_json=q.options_json,
            correct_answer=q.correct_answer,
            difficulty=q.difficulty,
        )
        questions.append(question)

    await repo.add_questions(questions)

    return CustomQuizResponse(
        id=quiz.id,
        subject_code=data.subject_code,
        unit_number=data.unit_number,
        mode=data.mode,
        question_count=len(questions),
    )
