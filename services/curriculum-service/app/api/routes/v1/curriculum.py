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


# ── Study Materials ──

@router.get("/materials")
async def list_materials(
    subject_code: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List study materials, optionally filtered by subject."""
    from app.models import StudyMaterial
    from sqlalchemy import select

    query = select(StudyMaterial).order_by(StudyMaterial.id.desc())
    if subject_code:
        query = query.where(StudyMaterial.subject_code == subject_code)
    result = await db.execute(query)
    materials = result.scalars().all()
    return [
        {
            "id": m.id,
            "subject_code": m.subject_code,
            "unit_number": m.unit_number,
            "title": m.title,
            "material_type": m.material_type,
            "url": m.url,
            "description": m.description,
            "created_at": m.created_at,
        }
        for m in materials
    ]


@router.post("/admin/materials", status_code=201)
async def add_material(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """Admin: add a study material (video, PDF link, notes)."""
    from app.models import StudyMaterial
    from datetime import datetime

    material = StudyMaterial(
        subject_code=data["subject_code"],
        unit_number=data.get("unit_number"),
        title=data["title"],
        material_type=data["material_type"],
        url=data["url"],
        description=data.get("description", ""),
        created_at=datetime.now().isoformat()[:19],
    )
    db.add(material)
    await db.commit()
    await db.refresh(material)
    return {"id": material.id, "title": material.title}


@router.delete("/admin/materials/{material_id}", status_code=204)
async def delete_material(material_id: int, db: AsyncSession = Depends(get_db)):
    """Admin: delete a study material."""
    from app.models import StudyMaterial
    from sqlalchemy import select, delete as sql_delete

    result = await db.execute(select(StudyMaterial).where(StudyMaterial.id == material_id))
    mat = result.scalar_one_or_none()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    await db.delete(mat)
    await db.commit()
