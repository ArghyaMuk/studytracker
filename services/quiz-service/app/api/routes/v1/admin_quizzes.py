import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.models import Quiz, QuizQuestion, QuizAttempt
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


@router.delete("/{quiz_id}", status_code=204)
async def delete_quiz(quiz_id: int, db: AsyncSession = Depends(get_db)):
    """Admin endpoint to delete a quiz and all its questions/attempts."""
    # Check quiz exists
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

    # Delete attempts, questions, then quiz
    await db.execute(delete(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id))
    await db.execute(delete(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id))
    await db.execute(delete(Quiz).where(Quiz.id == quiz_id))
    await db.commit()


@router.delete("/by-subject/{subject_code}", status_code=204)
async def delete_quizzes_by_subject(subject_code: str, db: AsyncSession = Depends(get_db)):
    """Admin endpoint to delete all quizzes for a subject code."""
    result = await db.execute(select(Quiz.id).where(Quiz.subject_code == subject_code))
    quiz_ids = [row[0] for row in result.all()]

    if quiz_ids:
        await db.execute(delete(QuizAttempt).where(QuizAttempt.quiz_id.in_(quiz_ids)))
        await db.execute(delete(QuizQuestion).where(QuizQuestion.quiz_id.in_(quiz_ids)))
        await db.execute(delete(Quiz).where(Quiz.id.in_(quiz_ids)))
        await db.commit()
