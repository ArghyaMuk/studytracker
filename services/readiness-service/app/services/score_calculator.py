"""Readiness score calculator using transparent weighted formula.

score = quiz_accuracy * W1 + pyq_accuracy * W2 + review_currency * W3
        + unit_coverage * W4 + consistency * W5 + days_remaining * W6

All signals normalized to 0-100 before weighting.
Interface designed so a trained ML model can later replace this formula.
"""

import json
from dataclasses import dataclass


@dataclass
class SignalData:
    quiz_accuracy: float | None = None  # 0-100
    pyq_accuracy: float | None = None  # 0-100
    review_currency: float | None = None  # 0-100 (100 = all up-to-date)
    unit_coverage: float | None = None  # 0-100 (% of units touched)
    consistency: float | None = None  # 0-100 (% of last 14 days with sessions)
    days_remaining: float | None = None  # 0-100 (time pressure signal)


class ReadinessCalculator:
    """Weighted-formula readiness scoring. Interface for future ML model swap."""

    # Default weights (semester_exam goal)
    DEFAULT_WEIGHTS = {
        "quiz_accuracy": 0.25,
        "pyq_accuracy": 0.20,
        "review_currency": 0.20,
        "unit_coverage": 0.15,
        "consistency": 0.10,
        "days_remaining": 0.10,
    }

    # Placement/competitive exam weights
    PLACEMENT_WEIGHTS = {
        "quiz_accuracy": 0.25,
        "pyq_accuracy": 0.30,
        "review_currency": 0.20,
        "unit_coverage": 0.15,
        "consistency": 0.10,
        "days_remaining": 0.00,
    }

    def compute(self, signals: SignalData, goal_type: str = "semester_exam") -> tuple[float, str]:
        """Compute readiness score.

        Returns (score 0-100, breakdown_json).
        Signals with None data are excluded and weight redistributed.
        """
        weights = (
            self.PLACEMENT_WEIGHTS.copy()
            if goal_type in ("placement_prep", "competitive_exam")
            else self.DEFAULT_WEIGHTS.copy()
        )

        # Collect available signals
        available = {}
        signal_dict = {
            "quiz_accuracy": signals.quiz_accuracy,
            "pyq_accuracy": signals.pyq_accuracy,
            "review_currency": signals.review_currency,
            "unit_coverage": signals.unit_coverage,
            "consistency": signals.consistency,
            "days_remaining": signals.days_remaining,
        }

        total_weight = 0.0
        for key, value in signal_dict.items():
            if value is not None and weights[key] > 0:
                available[key] = value
                total_weight += weights[key]

        if not available:
            return 0.0, json.dumps({"message": "insufficient_data"})

        # Redistribute weights proportionally
        score = 0.0
        breakdown = {}
        for key, value in available.items():
            normalized_weight = weights[key] / total_weight
            contribution = value * normalized_weight
            score += contribution
            breakdown[key] = {
                "raw_value": round(value, 2),
                "weight": round(normalized_weight, 3),
                "contribution": round(contribution, 2),
            }

        final_score = max(0, min(100, round(score)))
        breakdown["final_score"] = final_score
        return float(final_score), json.dumps(breakdown)
