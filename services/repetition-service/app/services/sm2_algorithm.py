"""
Spaced Repetition Algorithm (simplified SM-2 variant).

Implements an interval-ladder approach to schedule review cards:
- Forgot → reset to day 1.
- Barely remembered → stay at the same ladder level.
- Normal recall → advance one level (longer interval).
- Too easy → skip a level for even longer spacing.

The ladder is exam-aware: when an exam is approaching and units remain,
intervals are compressed so all material gets reviewed in time.
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class SM2Result:
    """Output of a single spaced-repetition computation."""
    ease_factor: float       # Kept for API compat; not used in simple mode
    interval_days: int       # Days until next review
    repetitions: int         # Current position on the interval ladder
    next_review_date: date   # Scheduled date for the next review


# ── Interval Ladder ──
# Each index represents a "level"; the value is the number of days until next review.
# Level 0 = 1 day, Level 1 = 3 days, ... up to Level 6 = 90 days.
# Successful recalls climb the ladder; failures reset to level 0.
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
    """Compute the next review date based on recall quality.

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

    # ── Determine new ladder position based on recall quality ──

    if quality <= 1:
        # Complete failure – reset to the bottom of the ladder
        new_repetitions = 0
        new_interval = 1
    elif quality == 2:
        # Marginal recall – repeat at the same interval to reinforce
        new_repetitions = repetitions
        new_interval = INTERVAL_LADDER[min(repetitions, len(INTERVAL_LADDER) - 1)]
    elif quality == 5:
        # Effortless recall – skip one ladder level to avoid wasting time
        new_repetitions = min(repetitions + 2, len(INTERVAL_LADDER) - 1)
        new_interval = INTERVAL_LADDER[new_repetitions]
    else:
        # Quality 3 or 4: solid recall – advance one level on the ladder
        new_repetitions = min(repetitions + 1, len(INTERVAL_LADDER) - 1)
        new_interval = INTERVAL_LADDER[new_repetitions]

    # ── Exam-aware compression ──
    # If an exam is upcoming and there are still units to review, cap the interval
    # so the student cycles through all remaining material before the exam date.
    if exam_date and units_remaining:
        days_until_exam = (exam_date - review_date).days
        if days_until_exam > 0 and units_remaining > 0:
            # Evenly distribute remaining days across remaining units
            max_interval = max(1, days_until_exam // units_remaining)
            new_interval = min(new_interval, max_interval)

    next_review = review_date + timedelta(days=new_interval)

    return SM2Result(
        ease_factor=1.0,  # Placeholder; simple mode doesn't use ease factor
        interval_days=new_interval,
        repetitions=new_repetitions,
        next_review_date=next_review,
    )
