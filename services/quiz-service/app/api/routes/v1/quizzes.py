from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import CurriculumClient, LLMClient
from app.core.db import get_db
from app.models import Quiz
from app.repositories import QuizRepository
from app.schemas import (
    QuizGenerateRequest,
    QuizResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services import QuizService

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
    return QuizService(
        repo=QuizRepository(db),
        curriculum_client=CurriculumClient(),
        llm_client=LLMClient(),
    )


@router.get("/available")
async def list_available_quizzes(
    subject_code: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all quizzes available for students to take."""
    from sqlalchemy.orm import selectinload

    query = select(Quiz).options(selectinload(Quiz.questions)).order_by(Quiz.created_at.desc())
    if subject_code:
        query = query.where(Quiz.subject_code == subject_code)
    result = await db.execute(query)
    quizzes = result.scalars().all()
    return [
        {
            "id": q.id,
            "subject_code": q.subject_code,
            "unit_number": q.unit_number,
            "mode": q.mode,
            "source_type": q.source_type,
            "question_count": len(q.questions),
            "created_at": q.created_at.isoformat() if q.created_at else None,
        }
        for q in quizzes
        if len(q.questions) > 0  # Only show quizzes that have questions
    ]


@router.post("/generate", response_model=QuizResponse, status_code=201)
async def generate_quiz(
    data: QuizGenerateRequest,
    user_id: int = Query(...),
    service: QuizService = Depends(get_quiz_service),
):
    return await service.generate_quiz(user_id, data)


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: int, service: QuizService = Depends(get_quiz_service)):
    return await service.get_quiz(quiz_id)


@router.post("/{quiz_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    quiz_id: int,
    data: QuizSubmitRequest,
    user_id: int = Query(...),
    service: QuizService = Depends(get_quiz_service),
):
    return await service.submit_quiz(quiz_id, user_id, data)
