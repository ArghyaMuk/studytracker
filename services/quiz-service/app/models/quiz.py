from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    subject_code = Column(String(50), nullable=False)
    unit_number = Column(Integer, nullable=True)
    source_type = Column(
        Enum("unit", "notes", "pyq", "weak_area", name="source_type_enum"), nullable=False
    )
    mode = Column(Enum("mcq", "viva", name="quiz_mode_enum"), default="mcq")
    created_at = Column(DateTime, server_default=func.now())

    questions = relationship("QuizQuestion", back_populates="quiz")
    attempts = relationship("QuizAttempt", back_populates="quiz")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question = Column(Text, nullable=False)
    options_json = Column(Text, nullable=True)  # JSON array of options for MCQ
    correct_answer = Column(Text, nullable=False)
    difficulty = Column(String(20), default="medium")
    source_pyq_year = Column(Integer, nullable=True)

    quiz = relationship("Quiz", back_populates="questions")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    submitted_at = Column(DateTime, server_default=func.now())

    quiz = relationship("Quiz", back_populates="attempts")


class PYQUpload(Base):
    __tablename__ = "pyq_uploads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_code = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    exam_type = Column(Enum("internal", "external", name="pyq_exam_type_enum"), nullable=True)
    file_path = Column(String(500), nullable=False)
    parsed_status = Column(
        Enum("pending", "processing", "completed", "failed", name="parsed_status_enum"),
        default="pending",
    )
    created_at = Column(DateTime, server_default=func.now())
