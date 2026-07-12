import json
import logging

from fastapi import HTTPException, status

from app.clients import CurriculumClient, LLMClient, QuizGeneratorInterface
from app.models import Quiz, QuizAttempt, QuizQuestion
from app.repositories import QuizRepository
from app.schemas import QuizGenerateRequest, QuizSubmitRequest

logger = logging.getLogger(__name__)


class QuizService:
    def __init__(
        self,
        repo: QuizRepository,
        curriculum_client: CurriculumClient,
        llm_client: QuizGeneratorInterface | None = None,
    ):
        self.repo = repo
        self.curriculum_client = curriculum_client
        self.llm_client = llm_client or LLMClient()

    async def generate_quiz(self, user_id: int, data: QuizGenerateRequest) -> Quiz:
        """Generate a quiz from various sources."""
        # Fetch subject info (name + unit topics) from Curriculum Service
        subject_info = await self.curriculum_client.get_subject_with_name(data.subject_code)
        subject_name = subject_info.get("name", data.subject_code)
        units = subject_info.get("units", [])

        # Build a meaningful topic and context for the LLM
        unit_title = ""
        context = ""
        if units and data.unit_number:
            for u in units:
                if u.get("unit_number") == data.unit_number:
                    unit_title = u.get("unit_title", "")
                    # Parse topics from topics_json
                    topics_raw = u.get("topics_json", "")
                    if topics_raw:
                        try:
                            import json as _json
                            topics_list = _json.loads(topics_raw)
                            context = f"Topics to cover: {', '.join(topics_list)}"
                        except (ValueError, TypeError):
                            context = f"Topics: {topics_raw}"
                    else:
                        context = f"Unit content: {unit_title}"
                    break

        # Build topic as the actual subject name + unit title (not the code)
        if unit_title:
            topic = f"{subject_name} - {unit_title}"
        else:
            topic = subject_name

        # Determine source type
        if data.pyq_upload_id:
            source_type = "pyq"
        elif data.notes_text:
            source_type = "notes"
            context = data.notes_text[:2000]  # Limit context length
        else:
            source_type = "unit"

        # Generate questions via LLM
        try:
            if data.mode == "viva":
                raw_questions = await self.llm_client.generate_viva_questions(
                    topic=topic, context=context, count=data.count
                )
            else:
                raw_questions = await self.llm_client.generate_mcq_questions(
                    topic=topic, context=context, count=data.count, difficulty=data.difficulty
                )
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e),
                headers={"Retry-After": "30"},
            )

        # Create quiz record
        quiz = Quiz(
            user_id=user_id,
            subject_code=data.subject_code,
            unit_number=data.unit_number,
            source_type=source_type,
            mode=data.mode,
        )
        quiz = await self.repo.create_quiz(quiz)

        # Create question records
        questions = []
        for q in raw_questions:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question=q.get("question", ""),
                options_json=json.dumps(q.get("options")) if q.get("options") else None,
                correct_answer=q.get("correct_answer", ""),
                difficulty=q.get("difficulty", data.difficulty),
            )
            questions.append(question)

        if questions:
            await self.repo.add_questions(questions)

        # Reload with questions
        return await self.repo.get_quiz_by_id(quiz.id)

    async def get_quiz(self, quiz_id: int) -> Quiz:
        quiz = await self.repo.get_quiz_by_id(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")
        return quiz

    async def submit_quiz(self, quiz_id: int, user_id: int, data: QuizSubmitRequest) -> dict:
        """Grade a quiz submission."""
        quiz = await self.repo.get_quiz_by_id(quiz_id)
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found")

        correct_count = 0
        feedback = []
        for question in quiz.questions:
            user_answer = data.answers.get(question.id, "")
            is_correct = user_answer.strip().lower() == question.correct_answer.strip().lower()
            if is_correct:
                correct_count += 1
            feedback.append({
                "question_id": question.id,
                "correct": is_correct,
                "correct_answer": question.correct_answer,
                "your_answer": user_answer,
            })

        total = len(quiz.questions)
        score = (correct_count / total * 100) if total > 0 else 0

        # Save attempt
        attempt = QuizAttempt(quiz_id=quiz_id, user_id=user_id, score=score)
        await self.repo.create_attempt(attempt)

        return {
            "quiz_id": quiz_id,
            "score": score,
            "total_questions": total,
            "correct_count": correct_count,
            "feedback": feedback,
        }
