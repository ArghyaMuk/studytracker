"""Unit tests for the readiness score calculator."""

import json


from app.services.score_calculator import ReadinessCalculator, SignalData


class TestReadinessCalculator:
    """Test weighted-formula readiness scoring."""

    def setup_method(self):
        self.calculator = ReadinessCalculator()

    def test_all_signals_perfect(self):
        """All signals at 100 should give score of 100."""
        signals = SignalData(
            quiz_accuracy=100,
            pyq_accuracy=100,
            review_currency=100,
            unit_coverage=100,
            consistency=100,
            days_remaining=100,
        )
        score, _ = self.calculator.compute(signals)
        assert score == 100

    def test_all_signals_zero(self):
        """All signals at 0 should give score of 0."""
        signals = SignalData(
            quiz_accuracy=0,
            pyq_accuracy=0,
            review_currency=0,
            unit_coverage=0,
            consistency=0,
            days_remaining=0,
        )
        score, _ = self.calculator.compute(signals)
        assert score == 0

    def test_no_data_returns_zero(self):
        """No available signals returns 0 with insufficient_data message."""
        signals = SignalData()
        score, breakdown = self.calculator.compute(signals)
        assert score == 0.0
        assert "insufficient_data" in breakdown

    def test_partial_signals_redistribute_weights(self):
        """Missing signals should have their weight redistributed."""
        signals = SignalData(quiz_accuracy=80, pyq_accuracy=60)
        score, breakdown_json = self.calculator.compute(signals)
        breakdown = json.loads(breakdown_json)
        # Weights should sum to 1.0 across available signals
        total_weight = sum(v["weight"] for k, v in breakdown.items() if k != "final_score")
        assert abs(total_weight - 1.0) < 0.01
        assert score > 0

    def test_placement_prep_weights(self):
        """Placement prep should increase PYQ weight and zero out days_remaining."""
        signals = SignalData(
            quiz_accuracy=80,
            pyq_accuracy=80,
            review_currency=80,
            unit_coverage=80,
            consistency=80,
            days_remaining=0,  # Should not matter for placement
        )
        semester_score, _ = self.calculator.compute(signals, "semester_exam")
        placement_score, _ = self.calculator.compute(signals, "placement_prep")
        # With days_remaining=0 and increased PYQ weight, scores differ
        assert placement_score != semester_score

    def test_score_clamped_0_100(self):
        """Score should always be between 0 and 100."""
        signals = SignalData(quiz_accuracy=150)  # Above normal range
        score, _ = self.calculator.compute(signals)
        assert 0 <= score <= 100

    def test_breakdown_contains_contributions(self):
        """Breakdown JSON should show per-signal contributions."""
        signals = SignalData(quiz_accuracy=75, consistency=60)
        _, breakdown_json = self.calculator.compute(signals)
        breakdown = json.loads(breakdown_json)
        assert "quiz_accuracy" in breakdown
        assert "consistency" in breakdown
        assert "raw_value" in breakdown["quiz_accuracy"]
        assert "weight" in breakdown["quiz_accuracy"]
        assert "contribution" in breakdown["quiz_accuracy"]
