"""Simple Spaced Repetition Algorithm.

A straightforward interval-based system:
- Got it wrong? Review tomorrow.
- Got it with difficulty? Review in a few days.
- Got it easily? Push review further out.

The interval grows as you keep getting it right, and resets when you forget.
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class SM2Result:
    ease_factor: float
    interval_days: int
    repetitions: int
    next_review_date: date


# Simple interval ladder: each successful recall moves to the next level
INTERVAL_LADDER = [1, 3, 7, 14, 30, 60, 90]


def compute_sm2(
    quality: int,
    ease_factor: float,
    interval_days: int,
    repetitions: int,
    review_date: date | None = None,
    exam_date: date | None = None,
    units_remaining: int | None = None,
) -> SM2Result:
    """Compute next review date using a simple spaced repetition system.

    Quality scale (how well did you recall?):
        0-1 = Forgot completely → reset to day 1
        2   = Barely remembered → stay at same level
        3   = Remembered with effort → move up 1 level
        4   = Remembered well → move up 1 level
        5   = Too easy → skip a level

    Args:
        quality: Recall quality rating 0-5
        ease_factor: Not used in simple mode (kept for API compatibility)
        interval_days: Current interval in days
        repetitions: Current level in the interval ladder
        review_date: Date of this review (defaults to today)
        exam_date: Optional exam date — shortens intervals near exams
        units_remaining: Number of units left to cover before exam
    """
    if review_date is None:
        review_date = date.today()

    if quality <= 1:
        # Forgot → reset to beginning
        new_repetitions = 0
        new_interval = 1
    elif quality == 2:
        # Barely remembered → repeat at same interval
        new_repetitions = repetitions
        new_interval = INTERVAL_LADDER[min(repetitions, len(INTERVAL_LADDER) - 1)]
    elif quality == 5:
        # Too easy → skip ahead
        new_repetitions = min(repetitions + 2, len(INTERVAL_LADDER) - 1)
        new_interval = INTERVAL_LADDER[new_repetitions]
    else:
        # Normal recall (3 or 4) → move to next level
        new_repetitions = min(repetitions + 1, len(INTERVAL_LADDER) - 1)
        new_interval = INTERVAL_LADDER[new_repetitions]

    # Exam-aware: shorten intervals when exam is close
    if exam_date and units_remaining:
        days_until_exam = (exam_date - review_date).days
        if days_until_exam > 0 and units_remaining > 0:
            # Ensure all units can be reviewed before the exam
            max_interval = max(1, days_until_exam // units_remaining)
            new_interval = min(new_interval, max_interval)

    next_review = review_date + timedelta(days=new_interval)

    return SM2Result(
        ease_factor=1.0,  # Not used in simple mode
        interval_days=new_interval,
        repetitions=new_repetitions,
        next_review_date=next_review,
    )
