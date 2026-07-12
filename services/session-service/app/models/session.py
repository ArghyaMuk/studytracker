from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class StudySession(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject_code = Column(String(50), nullable=False, index=True)
    unit_number = Column(Integer, nullable=False)
    started_at = Column(DateTime, server_default=func.now())
    duration_min = Column(Integer, nullable=False)
    focus_rating = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
