from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    total_semesters = Column(Integer, nullable=False)

    subjects = relationship("Subject", back_populates="program")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    semester = Column(Integer, nullable=False)
    type = Column(Enum("theory", "lab", name="subject_type_enum"), nullable=False)
    credits = Column(Integer, default=3)

    program = relationship("Program", back_populates="subjects")
    units = relationship("SubjectUnit", back_populates="subject", order_by="SubjectUnit.unit_number")


class SubjectUnit(Base):
    __tablename__ = "subject_units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    unit_title = Column(String(300), nullable=False)
    topics_json = Column(Text, nullable=True)  # JSON array of topic keywords

    subject = relationship("Subject", back_populates="units")


class UniversityTemplate(Base):
    __tablename__ = "university_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    university_name = Column(String(200), nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    semester = Column(Integer, nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)


class StudyMaterial(Base):
    __tablename__ = "study_materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_code = Column(String(50), nullable=False, index=True)
    unit_number = Column(Integer, nullable=True)
    title = Column(String(300), nullable=False)
    material_type = Column(Enum("video", "pdf", "link", "notes", name="material_type_enum"), nullable=False)
    url = Column(Text, nullable=False)  # YouTube URL, PDF path, or external link
    description = Column(Text, nullable=True)
    created_at = Column(String(30), nullable=True)


class ExamSchedule(Base):
    __tablename__ = "exam_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_code = Column(String(50), nullable=False, index=True)
    subject_name = Column(String(200), nullable=True)
    exam_type = Column(Enum("internal", "external", "lab_viva", "assignment", name="exam_schedule_type_enum"), nullable=False)
    exam_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    exam_time = Column(String(10), nullable=True)   # HH:MM
    duration_minutes = Column(Integer, nullable=True)
    venue = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    quiz_id = Column(Integer, nullable=True)  # Linked quiz for online exam
    created_at = Column(String(30), nullable=True)


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=True)
    subject_code = Column(String(50), nullable=False, index=True)
    subject_name = Column(String(200), nullable=True)
    enrolled_at = Column(String(30), nullable=True)
