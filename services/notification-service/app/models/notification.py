from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    daily_digest_enabled = Column(Boolean, default=True)
    readiness_alert_enabled = Column(Boolean, default=True)
    exam_countdown_enabled = Column(Boolean, default=True)
    inactivity_nudge_enabled = Column(Boolean, default=True)
    preferred_time = Column(String(5), default="08:00")  # HH:MM format


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(
        Enum("daily_digest", "readiness_alert", "exam_countdown", "inactivity_nudge",
             name="notification_type_enum"),
        nullable=False,
    )
    subject_code = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    channel = Column(String(50), default="in_app")
    status = Column(
        Enum("sent", "failed", "pending", name="notification_status_enum"),
        default="pending",
    )
    sent_at = Column(DateTime, server_default=func.now())
    retry_count = Column(Integer, default=0)
