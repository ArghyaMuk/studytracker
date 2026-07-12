"""SM-2 Spaced Repetition Algorithm implementation.

Reference: SuperMemo 2 algorithm by Piotr Wozniak.
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class SM2Result:
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: date


def compute_sm2(
    quality: int,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    review_date: date | None = None,
    exam_date: date | None = None,
    units_remaining: int | None = None,
) -> SM2Result:
    """Compute next review parameters using SM-2 algorithm.

    Args:
        quality: Recall quality rating 0-5
        ease_factor: Current easiness factor (minimum 1.3)
        interval_days: Current interval in days
        repetitions: Number of successful repetitions
        review_date: Date of this review (defaults to today)
        exam_date: Optional exam date for interval capping
        units_remaining: Optional number of unreviewed units for exam-aware scheduling
    """
    if review_date is None:
        review_date = date.today()

    # SM-2 formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ef = max(1.3, new_ef)  # EF floor

    if quality < 3:
        # Failed recall - reset
        new_repetitions = 0
        new_interval = 1
    else:
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval_days * new_ef)
        new_repetitions = repetitions + 1

    # Exam-aware capping
    if exam_date and units_remaining:
        days_until_exam = (exam_date - review_date).days
        if days_until_exam > 0 and units_remaining > 0:
            max_interval = days_until_exam // units_remaining
            max_interval = max(1, max_interval)
            new_interval = min(new_interval, max_interval)

    next_review = review_date + timedelta(days=new_interval)

    return SM2Result(
        ease_factor=new_ef,
        interval_days=new_interval,
        repetitions=new_repetitions,
        next_review_date=next_review,
    )
