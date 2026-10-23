"""
EngageIQ Data Pipeline - OPI Calculator
Output Productivity Index (Tangible Work Delivery).
Weights: Completion (25%), Velocity (25%), Deadlines (20%), Activity (20%), Rework Penalty (10%).
"""

from typing import Dict, Any


def compute_opi(
    completion_rate: float,
    velocity: float,
    deadline_adherence: float,
    code_activity: float,
    rework_ratio: float,
    w1: float = 0.25,
    w2: float = 0.25,
    w3: float = 0.20,
    w4: float = 0.20,
    w5: float = 0.10,
) -> float:
    """
    Computes the Output Productivity Index (OPI).
    
    Formula:
        OPI = (W1*completion + W2*velocity + W3*deadlines + W4*activity) - (W5*rework)
    """
    positive_delivery = (
        (w1 * completion_rate) +
        (w2 * velocity) +
        (w3 * deadline_adherence) +
        (w4 * code_activity)
    )
    rework_penalty = w5 * rework_ratio
    opi = positive_delivery - rework_penalty
    return round(max(0.0, min(1.0, float(opi))), 4)


def compute_opi_breakdown(
    completion_rate: float,
    velocity: float,
    deadline_adherence: float,
    code_activity: float,
    rework_ratio: float
) -> Dict[str, Any]:
    """Provides detailed feature-level breakdown for explainability."""
    score = compute_opi(completion_rate, velocity, deadline_adherence, code_activity, rework_ratio)
    return {
        "opi_score": score,
        "features": {
            "completion_rate": {
                "value": completion_rate,
                "weight": 0.25,
                "contribution": round(0.25 * completion_rate, 4),
            },
            "velocity": {
                "value": velocity,
                "weight": 0.25,
                "contribution": round(0.25 * velocity, 4),
            },
            "deadline_adherence": {
                "value": deadline_adherence,
                "weight": 0.20,
                "contribution": round(0.20 * deadline_adherence, 4),
            },
            "code_activity": {
                "value": code_activity,
                "weight": 0.20,
                "contribution": round(0.20 * code_activity, 4),
            },
            "rework_ratio": {
                "value": rework_ratio,
                "weight": -0.10,
                "penalty": round(0.10 * rework_ratio, 4),
            },
        }
    }
