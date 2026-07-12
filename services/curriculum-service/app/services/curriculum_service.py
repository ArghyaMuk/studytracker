from fastapi import HTTPException, status

from app.models import Program, Subject, SubjectUnit
from app.repositories import CurriculumRepository
from app.schemas.curriculum import ProgramCreate, SubjectCreate


class CurriculumService:
    def __init__(self, repo: CurriculumRepository):
        self.repo = repo

    async def get_all_programs(self) -> list[Program]:
        return await self.repo.get_all_programs()

    async def create_program(self, data: ProgramCreate) -> Program:
        program = Program(name=data.name, total_semesters=data.total_semesters)
        return await self.repo.create_program(program)

    async def get_subjects_for_semester(self, program_id: int, semester: int) -> list[Subject]:
        program = await self.repo.get_program_by_id(program_id)
        if not program:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
        return await self.repo.get_subjects_by_program_semester(program_id, semester)

    async def get_subject_units(self, code: str) -> list[SubjectUnit]:
        subject = await self.repo.get_subject_by_code(code)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        return subject.units

    async def create_subject(self, program_id: int, data: SubjectCreate) -> Subject:
        program = await self.repo.get_program_by_id(program_id)
        if not program:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

        if data.type == "theory" and len(data.units) < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Theory subjects must have at least one unit",
            )

        if len(data.units) > 20:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="A subject cannot have more than 20 units",
            )

        subject = Subject(
            program_id=program_id,
            code=data.code,
            name=data.name,
            semester=data.semester,
            type=data.type,
            credits=data.credits,
        )

        for unit_data in data.units:
            unit = SubjectUnit(
                unit_number=unit_data.unit_number,
                unit_title=unit_data.unit_title,
                topics_json=unit_data.topics_json,
            )
            subject.units.append(unit)

        return await self.repo.create_subject(subject)

    async def delete_program(self, program_id: int) -> None:
        program = await self.repo.get_program_by_id(program_id)
        if not program:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
        await self.repo.delete_program(program)

    async def delete_subject(self, subject_id: int) -> None:
        subject = await self.repo.get_subject_by_id(subject_id)
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
        await self.repo.delete_subject(subject)
