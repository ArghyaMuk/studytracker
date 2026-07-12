from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.repositories import CurriculumRepository
from app.schemas import (
    ProgramCreate,
    ProgramResponse,
    SubjectCreate,
    SubjectResponse,
    SubjectUnitResponse,
)
from app.services import CurriculumService

router = APIRouter(tags=["curriculum"])


def get_curriculum_service(db: AsyncSession = Depends(get_db)) -> CurriculumService:
    return CurriculumService(CurriculumRepository(db))


@router.get("/programs", response_model=list[ProgramResponse])
async def list_programs(service: CurriculumService = Depends(get_curriculum_service)):
    return await service.get_all_programs()


@router.post("/admin/programs", response_model=ProgramResponse, status_code=201)
async def create_program(
    data: ProgramCreate, service: CurriculumService = Depends(get_curriculum_service)
):
    return await service.create_program(data)


@router.delete("/admin/programs/{program_id}", status_code=204)
async def delete_program(
    program_id: int, service: CurriculumService = Depends(get_curriculum_service)
):
    await service.delete_program(program_id)


@router.get("/programs/{program_id}/semesters/{semester}/subjects", response_model=list[SubjectResponse])
async def get_semester_subjects(
    program_id: int,
    semester: int,
    service: CurriculumService = Depends(get_curriculum_service),
):
    return await service.get_subjects_for_semester(program_id, semester)


@router.get("/subjects/{code}/units", response_model=list[SubjectUnitResponse])
async def get_subject_units(
    code: str, service: CurriculumService = Depends(get_curriculum_service)
):
    return await service.get_subject_units(code)


@router.post("/admin/programs/{program_id}/subjects", response_model=SubjectResponse, status_code=201)
async def create_subject(
    program_id: int,
    data: SubjectCreate,
    service: CurriculumService = Depends(get_curriculum_service),
):
    return await service.create_subject(program_id, data)


@router.delete("/admin/subjects/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: int, service: CurriculumService = Depends(get_curriculum_service)
):
    await service.delete_subject(subject_id)
