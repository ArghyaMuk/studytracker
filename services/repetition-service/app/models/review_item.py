from sqlalchemy import Column, Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject_code = Column(String(50), nullable=False, index=True)
    unit_number = Column(Integer, nullable=False)
    ease_factor = Column(Float, default=2.5)
    interval_days = Column(Integer, default=1)
    repetitions = Column(Integer, default=0)
    next_review_date = Column(Date, nullable=False)
    last_reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
