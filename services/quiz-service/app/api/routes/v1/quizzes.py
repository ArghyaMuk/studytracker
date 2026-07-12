from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients import CurriculumClient, LLMClient
from app.core.db import get_db
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
