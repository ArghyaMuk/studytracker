from fastapi import APIRouter, Depends, Header, HTTPException, status
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


async def require_admin(x_user_role: str = Header("student", alias="X-User-Role")) -> str:
    if x_user_role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return x_user_role


@router.get("/programs", response_model=list[ProgramResponse])
async def list_programs(service: CurriculumService = Depends(get_curriculum_service)):
    return await service.get_all_programs()


@router.post("/admin/programs", response_model=ProgramResponse, status_code=201)
async def create_program(
    data: ProgramCreate,
    _: str = Depends(require_admin),
    service: CurriculumService = Depends(get_curriculum_service),
):
    return await service.create_program(data)


@router.delete("/admin/programs/{program_id}", status_code=204)
async def delete_program(
    program_id: int,
    _: str = Depends(require_admin),
    service: CurriculumService = Depends(get_curriculum_service),
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
    _: str = Depends(require_admin),
    service: CurriculumService = Depends(get_curriculum_service),
):
    return await service.create_subject(program_id, data)


@router.delete("/admin/subjects/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: int,
    _: str = Depends(require_admin),
    service: CurriculumService = Depends(get_curriculum_service),
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
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: add a study material (video, PDF link, notes)."""
    from app.models import StudyMaterial
    from datetime import datetime

    # Validate required fields
    if not data.get("subject_code") or not data.get("title") or not data.get("url") or not data.get("material_type"):
        raise HTTPException(status_code=422, detail="subject_code, title, url, and material_type are required")

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
async def delete_material(
    material_id: int,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: delete a study material."""
    from app.models import StudyMaterial
    from sqlalchemy import select

    result = await db.execute(select(StudyMaterial).where(StudyMaterial.id == material_id))
    mat = result.scalar_one_or_none()
    if not mat:
        raise HTTPException(status_code=404, detail="Material not found")
    await db.delete(mat)
    await db.commit()


# ── Exam Schedule ──

@router.get("/exams")
async def list_exams(
    subject_code: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all scheduled exams, optionally filtered by subject."""
    from app.models import ExamSchedule
    from sqlalchemy import select

    query = select(ExamSchedule).order_by(ExamSchedule.exam_date.asc())
    if subject_code:
        query = query.where(ExamSchedule.subject_code == subject_code)
    result = await db.execute(query)
    exams = result.scalars().all()
    return [
        {
            "id": e.id,
            "subject_code": e.subject_code,
            "subject_name": e.subject_name,
            "exam_type": e.exam_type,
            "exam_date": e.exam_date,
            "exam_time": e.exam_time,
            "duration_minutes": e.duration_minutes,
            "venue": e.venue,
            "notes": e.notes,
            "quiz_id": e.quiz_id,
            "created_at": e.created_at,
        }
        for e in exams
    ]


@router.post("/admin/exams", status_code=201)
async def create_exam(
    data: dict,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: schedule an exam for a subject."""
    from app.models import ExamSchedule
    from datetime import datetime

    if not data.get("subject_code") or not data.get("exam_type") or not data.get("exam_date"):
        raise HTTPException(status_code=422, detail="subject_code, exam_type, and exam_date are required")

    exam = ExamSchedule(
        subject_code=data["subject_code"],
        subject_name=data.get("subject_name", ""),
        exam_type=data["exam_type"],
        exam_date=data["exam_date"],
        exam_time=data.get("exam_time"),
        duration_minutes=data.get("duration_minutes"),
        venue=data.get("venue", ""),
        notes=data.get("notes", ""),
        quiz_id=data.get("quiz_id"),
        created_at=datetime.now().isoformat()[:19],
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)
    return {"id": exam.id, "subject_code": exam.subject_code, "exam_date": exam.exam_date}


@router.delete("/admin/exams/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: int,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: delete a scheduled exam."""
    from app.models import ExamSchedule
    from sqlalchemy import select

    result = await db.execute(select(ExamSchedule).where(ExamSchedule.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    await db.delete(exam)
    await db.commit()


# ── Student Enrollment ──

@router.get("/enrollments")
async def list_enrollments(
    user_id: int = None,
    subject_code: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List enrollments, filtered by user_id or subject_code."""
    from app.models import StudentEnrollment
    from sqlalchemy import select

    query = select(StudentEnrollment)
    if user_id:
        query = query.where(StudentEnrollment.user_id == user_id)
    if subject_code:
        query = query.where(StudentEnrollment.subject_code == subject_code)
    result = await db.execute(query)
    enrollments = result.scalars().all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "user_email": e.user_email,
            "subject_code": e.subject_code,
            "subject_name": e.subject_name,
            "enrolled_at": e.enrolled_at,
        }
        for e in enrollments
    ]


@router.post("/admin/enrollments", status_code=201)
async def enroll_student(
    data: dict,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: enroll a student in a subject."""
    from app.models import StudentEnrollment
    from datetime import datetime
    from sqlalchemy import select

    if not data.get("user_id") or not data.get("subject_code"):
        raise HTTPException(status_code=422, detail="user_id and subject_code are required")

    # Check if already enrolled
    existing = await db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.user_id == data["user_id"],
            StudentEnrollment.subject_code == data["subject_code"],
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Student already enrolled in this subject")

    enrollment = StudentEnrollment(
        user_id=data["user_id"],
        user_email=data.get("user_email", ""),
        subject_code=data["subject_code"],
        subject_name=data.get("subject_name", ""),
        enrolled_at=datetime.now().isoformat()[:19],
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return {"id": enrollment.id, "user_id": enrollment.user_id, "subject_code": enrollment.subject_code}


@router.delete("/admin/enrollments/{enrollment_id}", status_code=204)
async def remove_enrollment(
    enrollment_id: int,
    _: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin: remove a student from a subject."""
    from app.models import StudentEnrollment
    from sqlalchemy import select

    result = await db.execute(select(StudentEnrollment).where(StudentEnrollment.id == enrollment_id))
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    await db.delete(enrollment)
    await db.commit()
