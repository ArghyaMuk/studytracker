"""Unit tests for the simple spaced repetition algorithm."""

from datetime import date

from app.services.sm2_algorithm import compute_sm2


class TestSpacedRepetition:
    """Test the simple interval-based repetition system."""

    def test_forgot_resets_to_day_1(self):
        """Quality 0 or 1 = forgot → review tomorrow."""
        result = compute_sm2(
            quality=0,
            ease_factor=1.0,
            interval_days=30,
            repetitions=4,
            review_date=date(2024, 1, 1),
        )
        assert result.interval_days == 1
        assert result.repetitions == 0
        assert result.next_review_date == date(2024, 1, 2)

    def test_barely_remembered_stays_same(self):
        """Quality 2 = barely remembered → repeat same interval."""
        result = compute_sm2(
            quality=2,
            ease_factor=1.0,
            interval_days=7,
            repetitions=2,  # Level 2 = 7 days
        )
        assert result.interval_days == 7
        assert result.repetitions == 2

    def test_good_recall_moves_up(self):
        """Quality 3 or 4 = good → move to next interval level."""
        result = compute_sm2(
            quality=4,
            ease_factor=1.0,
            interval_days=1,
            repetitions=0,  # Level 0 → Level 1
            review_date=date(2024, 1, 1),
        )
        assert result.interval_days == 3  # Ladder: 1 → 3
        assert result.repetitions == 1
        assert result.next_review_date == date(2024, 1, 4)

    def test_easy_skips_a_level(self):
        """Quality 5 = too easy → skip ahead."""
        result = compute_sm2(
            quality=5,
            ease_factor=1.0,
            interval_days=1,
            repetitions=0,  # Level 0 → Level 2
        )
        assert result.interval_days == 7  # Skipped to level 2
        assert result.repetitions == 2

    def test_interval_ladder_progression(self):
        """Normal recall moves through: 1 → 3 → 7 → 14 → 30 → 60 → 90."""
        intervals = []
        repetitions = 0
        for _ in range(6):
            result = compute_sm2(
                quality=4,
                ease_factor=1.0,
                interval_days=1,
                repetitions=repetitions,
            )
            intervals.append(result.interval_days)
            repetitions = result.repetitions

        assert intervals == [3, 7, 14, 30, 60, 90]

    def test_max_interval_caps_at_90(self):
        """Repetitions don't exceed the ladder length."""
        result = compute_sm2(
            quality=5,
            ease_factor=1.0,
            interval_days=90,
            repetitions=6,  # Already at max
        )
        assert result.interval_days == 90
        assert result.repetitions == 6  # Stays at max

    def test_exam_aware_shortens_interval(self):
        """Intervals are capped when exam is near."""
        result = compute_sm2(
            quality=4,
            ease_factor=1.0,
            interval_days=7,
            repetitions=3,  # Would give 14 days normally
            review_date=date(2024, 1, 1),
            exam_date=date(2024, 1, 6),  # 5 days away
            units_remaining=5,  # 5 units left
        )
        # max_interval = 5 days / 5 units = 1 day
        assert result.interval_days == 1

    def test_no_exam_no_capping(self):
        """Without exam date, intervals grow normally."""
        result = compute_sm2(
            quality=4,
            ease_factor=1.0,
            interval_days=7,
            repetitions=3,
            review_date=date(2024, 1, 1),
            exam_date=None,
            units_remaining=None,
        )
        assert result.interval_days == 30  # Level 3 → Level 4 = 30 days
