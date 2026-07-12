from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ReadinessScore(Base):
    __tablename__ = "readiness_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject_code = Column(String(50), nullable=False, index=True)
    unit_number = Column(Integer, nullable=True)  # NULL = subject-level score
    score = Column(Float, nullable=False, default=0.0)
    computed_at = Column(DateTime, server_default=func.now())
    breakdown_json = Column(Text, nullable=True)  # JSON with per-signal scores
