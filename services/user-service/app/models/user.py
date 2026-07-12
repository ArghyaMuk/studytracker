from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    college = Column(String(200), nullable=True)
    university = Column(String(200), nullable=True)
    program_id = Column(Integer, nullable=True)
    current_semester = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    profile = relationship("UserProfile", back_populates="user", uselist=False)
    exam_targets = relationship("ExamTarget", back_populates="user")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    daily_study_hours_target = Column(Float, default=2.0)
    goal_type = Column(
        Enum("semester_exam", "placement_prep", "competitive_exam", name="goal_type_enum"),
        default="semester_exam",
    )

    user = relationship("User", back_populates="profile")


class ExamTarget(Base):
    __tablename__ = "exam_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_code = Column(String(50), nullable=False)
    exam_type = Column(Enum("internal", "external", name="exam_type_enum"), nullable=False)
    exam_date = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="exam_targets")
