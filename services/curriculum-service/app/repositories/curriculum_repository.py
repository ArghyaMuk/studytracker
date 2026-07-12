from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Program, Subject, SubjectUnit


class CurriculumRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_programs(self) -> list[Program]:
        result = await self.db.execute(select(Program))
        return list(result.scalars().all())

    async def get_program_by_id(self, program_id: int) -> Program | None:
        result = await self.db.execute(select(Program).where(Program.id == program_id))
        return result.scalar_one_or_none()

    async def create_program(self, program: Program) -> Program:
        self.db.add(program)
        await self.db.commit()
        await self.db.refresh(program)
        return program

    async def get_subjects_by_program_semester(
        self, program_id: int, semester: int
    ) -> list[Subject]:
        result = await self.db.execute(
            select(Subject)
            .options(selectinload(Subject.units))
            .where(Subject.program_id == program_id, Subject.semester == semester)
        )
        return list(result.scalars().all())

    async def get_subject_by_code(self, code: str) -> Subject | None:
        result = await self.db.execute(
            select(Subject).options(selectinload(Subject.units)).where(Subject.code == code)
        )
        return result.scalar_one_or_none()

    async def create_subject(self, subject: Subject) -> Subject:
        self.db.add(subject)
        await self.db.commit()
        await self.db.refresh(subject, ["units"])
        return subject

    async def get_units_by_subject(self, subject_id: int) -> list[SubjectUnit]:
        result = await self.db.execute(
            select(SubjectUnit)
            .where(SubjectUnit.subject_id == subject_id)
            .order_by(SubjectUnit.unit_number)
        )
        return list(result.scalars().all())

    async def get_subject_by_id(self, subject_id: int) -> Subject | None:
        result = await self.db.execute(
            select(Subject).options(selectinload(Subject.units)).where(Subject.id == subject_id)
        )
        return result.scalar_one_or_none()

    async def delete_program(self, program: Program) -> None:
        # Delete all subjects and their units for this program
        subjects_result = await self.db.execute(
            select(Subject).where(Subject.program_id == program.id)
        )
        subjects = subjects_result.scalars().all()
        for subject in subjects:
            # Delete units
            units_result = await self.db.execute(
                select(SubjectUnit).where(SubjectUnit.subject_id == subject.id)
            )
            for unit in units_result.scalars().all():
                await self.db.delete(unit)
            await self.db.delete(subject)
        await self.db.delete(program)
        await self.db.commit()

    async def delete_subject(self, subject: Subject) -> None:
        # Delete units first
        units_result = await self.db.execute(
            select(SubjectUnit).where(SubjectUnit.subject_id == subject.id)
        )
        for unit in units_result.scalars().all():
            await self.db.delete(unit)
        await self.db.delete(subject)
        await self.db.commit()
