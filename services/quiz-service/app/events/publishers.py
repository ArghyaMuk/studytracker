from shared.events import EventPublisher, EventType


class QuizEventPublisher:
    """Publishes quiz.completed events."""

    def __init__(self, publisher: EventPublisher):
        self._publisher = publisher

    async def publish_quiz_completed(
        self,
        user_id: int,
        subject_code: str,
        unit_number: int,
        score_percentage: float,
        question_count: int,
        quiz_type: str,
    ) -> str:
        return await self._publisher.publish(
            EventType.QUIZ_COMPLETED,
            payload={
                "user_id": user_id,
                "subject_code": subject_code,
                "unit_number": unit_number,
                "score_percentage": score_percentage,
                "question_count": question_count,
                "quiz_type": quiz_type,
                "completion_timestamp": "",
            },
        )
