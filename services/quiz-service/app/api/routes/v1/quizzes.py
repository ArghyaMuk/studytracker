from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
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


@router.get("/history")
async def get_quiz_history(
    user_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get a user's quiz attempt history with scores."""
    from app.models import QuizAttempt
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(QuizAttempt)
        .options(selectinload(QuizAttempt.quiz))
        .where(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.submitted_at.desc())
    )
    attempts = result.scalars().all()
    return [
        {
            "id": a.id,
            "quiz_id": a.quiz_id,
            "subject_code": a.quiz.subject_code if a.quiz else "—",
            "unit_number": a.quiz.unit_number if a.quiz else 0,
            "score": round(a.score, 1),
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
        }
        for a in attempts
    ]


@router.post("/generate", response_model=QuizResponse, status_code=201)
async def generate_quiz(
    data: QuizGenerateRequest,
    x_user_id: str = Header(None, alias="X-User-Id"),
    x_user_role: str = Header("student", alias="X-User-Role"),
    service: QuizService = Depends(get_quiz_service),
):
    # Only admin can generate quizzes
    if x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required to generate quizzes")
    user_id = int(x_user_id) if x_user_id else 0
    return await service.generate_quiz(user_id, data)


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: int, service: QuizService = Depends(get_quiz_service)):
    return await service.get_quiz(quiz_id)


@router.post("/{quiz_id}/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    request: Request,
    quiz_id: int,
    data: QuizSubmitRequest,
    x_user_id: str = Header(None, alias="X-User-Id"),
    service: QuizService = Depends(get_quiz_service),
):
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = int(x_user_id)
    result = await service.submit_quiz(quiz_id, user_id, data)

    # Publish quiz.completed event
    publisher = getattr(request.app.state, "event_publisher", None)
    if publisher and result.get("score") is not None:
        try:
            quiz = await service.get_quiz(quiz_id)
            await publisher.publish_quiz_completed(
                user_id=user_id,
                subject_code=quiz.subject_code,
                unit_number=quiz.unit_number or 1,
                score_percentage=result["score"],
                question_count=result["total_questions"],
                quiz_type=quiz.source_type or "unit",
            )
        except Exception:
            pass  # Best-effort event publishing

    return result
