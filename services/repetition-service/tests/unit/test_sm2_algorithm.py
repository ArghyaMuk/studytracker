"""Unit tests for the SM-2 spaced repetition algorithm."""

from datetime import date, timedelta

import pytest

from app.services.sm2_algorithm import SM2Result, compute_sm2


class TestSM2Algorithm:
    """Test SM-2 algorithm implementation against spec requirements."""

    def test_initial_review_quality_5_perfect(self):
        """First perfect recall: interval should be 1 day."""
        result = compute_sm2(
            quality=5,
            ease_factor=2.5,
            interval_days=1,
            repetitions=0,
            review_date=date(2024, 1, 1),
        )
        assert result.interval_days == 1
        assert result.repetitions == 1
        assert result.ease_factor > 2.5  # EF increases on perfect recall
        assert result.next_review_date == date(2024, 1, 2)

    def test_second_review_quality_5(self):
        """Second perfect recall: interval should be 6 days."""
        result = compute_sm2(
            quality=5,
            ease_factor=2.6,
            interval_days=1,
            repetitions=1,
            review_date=date(2024, 1, 2),
        )
        assert result.interval_days == 6
        assert result.repetitions == 2
        assert result.next_review_date == date(2024, 1, 8)

    def test_third_review_uses_ease_factor(self):
        """Third+ review: interval = round(interval * EF)."""
        result = compute_sm2(
            quality=4,
            ease_factor=2.5,
            interval_days=6,
            repetitions=2,
            review_date=date(2024, 1, 8),
        )
        # interval = round(6 * EF_new)
        assert result.interval_days == round(6 * result.ease_factor)
        assert result.repetitions == 3

    def test_failed_recall_resets(self):
        """Quality < 3 resets repetitions and interval."""
        result = compute_sm2(
            quality=2,
            ease_factor=2.5,
            interval_days=15,
            repetitions=5,
        )
        assert result.repetitions == 0
        assert result.interval_days == 1

    def test_ease_factor_floor(self):
        """EF should never go below 1.3."""
        result = compute_sm2(
            quality=0,  # Worst recall
            ease_factor=1.3,
            interval_days=1,
            repetitions=0,
        )
        assert result.ease_factor == 1.3

    def test_ease_factor_calculation(self):
        """Verify EF formula: EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02))."""
        ef = 2.5
        q = 4
        expected_ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        result = compute_sm2(quality=q, ease_factor=ef, interval_days=6, repetitions=2)
        assert abs(result.ease_factor - expected_ef) < 0.001

    def test_exam_aware_capping(self):
        """Interval should be capped based on exam date and units remaining."""
        # Exam in 10 days, 5 units remaining: max interval = 10/5 = 2 days
        result = compute_sm2(
            quality=5,
            ease_factor=2.5,
            interval_days=6,
            repetitions=2,
            review_date=date(2024, 1, 1),
            exam_date=date(2024, 1, 11),
            units_remaining=5,
        )
        assert result.interval_days <= 2

    def test_exam_aware_no_capping_when_exam_far(self):
        """No capping when exam is far away."""
        result = compute_sm2(
            quality=5,
            ease_factor=2.5,
            interval_days=6,
            repetitions=2,
            review_date=date(2024, 1, 1),
            exam_date=date(2024, 6, 1),  # 5 months away
            units_remaining=5,
        )
        # Normal interval should be used (round(6 * EF))
        expected = round(6 * result.ease_factor)
        assert result.interval_days == min(expected, (date(2024, 6, 1) - date(2024, 1, 1)).days // 5)

    def test_quality_3_boundary(self):
        """Quality 3 is the boundary — still counts as success."""
        result = compute_sm2(
            quality=3,
            ease_factor=2.5,
            interval_days=1,
            repetitions=0,
        )
        assert result.repetitions == 1  # Incremented (not reset)
        assert result.interval_days == 1  # First successful repetition
