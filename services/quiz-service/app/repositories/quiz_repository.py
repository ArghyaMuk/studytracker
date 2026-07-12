from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import PYQUpload, Quiz, QuizAttempt, QuizQuestion


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_quiz(self, quiz: Quiz) -> Quiz:
        self.db.add(quiz)
        await self.db.commit()
        await self.db.refresh(quiz, ["questions"])
        return quiz

    async def get_quiz_by_id(self, quiz_id: int) -> Quiz | None:
        result = await self.db.execute(
            select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz_id)
        )
        return result.scalar_one_or_none()

    async def add_questions(self, questions: list[QuizQuestion]) -> None:
        self.db.add_all(questions)
        await self.db.commit()

    async def create_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def create_pyq_upload(self, upload: PYQUpload) -> PYQUpload:
        self.db.add(upload)
        await self.db.commit()
        await self.db.refresh(upload)
        return upload

    async def get_pyq_upload(self, upload_id: int) -> PYQUpload | None:
        result = await self.db.execute(
            select(PYQUpload).where(PYQUpload.id == upload_id)
        )
        return result.scalar_one_or_none()
