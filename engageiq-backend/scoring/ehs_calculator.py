"""
EngageIQ Data Pipeline - EHS Calculator
Employee Health Score (Engagement / Work-Pattern Health Index).
Weights: Meeting Load (30%), Focus Gap (30%), Response Latency (20%), After-Hours (20%).
"""

from typing import Dict, Any


def compute_ehs(
    meeting_load: float,
    focus_gap: float,
    response_latency: float,
    after_hours_ratio: float,
    w1: float = 0.30,
    w2: float = 0.30,
    w3: float = 0.20,
    w4: float = 0.20,
) -> float:
    """
    Computes the Employee Health Score (EHS).
    
    Inputs are normalized [0, 1] load metrics (where 1.0 = heavy load/friction).
    The formula subtracts the weighted load from 1.0, so 1.0 represents optimal work health.
    
    Formula:
        EHS = 1.0 - (W1 * meeting_load + W2 * focus_gap + W3 * response_latency + W4 * after_hours_ratio)
    """
    weighted_load = (
        (w1 * meeting_load) +
        (w2 * focus_gap) +
        (w3 * response_latency) +
        (w4 * after_hours_ratio)
    )
    ehs = 1.0 - weighted_load
    return round(max(0.0, min(1.0, float(ehs))), 4)


def compute_ehs_breakdown(
    meeting_load: float,
    focus_gap: float,
    response_latency: float,
    after_hours_ratio: float
) -> Dict[str, Any]:
    """Provides detailed feature-level breakdown for explainability."""
    score = compute_ehs(meeting_load, focus_gap, response_latency, after_hours_ratio)
    return {
        "ehs_score": score,
        "features": {
            "meeting_load": {
                "raw_normalized": meeting_load,
                "weight": 0.30,
                "penalty": round(0.30 * meeting_load, 4),
                "health_contribution": round(0.30 * (1.0 - meeting_load), 4),
            },
            "focus_gap": {
                "raw_normalized": focus_gap,
                "weight": 0.30,
                "penalty": round(0.30 * focus_gap, 4),
                "health_contribution": round(0.30 * (1.0 - focus_gap), 4),
            },
            "response_latency": {
                "raw_normalized": response_latency,
                "weight": 0.20,
                "penalty": round(0.20 * response_latency, 4),
                "health_contribution": round(0.20 * (1.0 - response_latency), 4),
            },
            "after_hours_ratio": {
                "raw_normalized": after_hours_ratio,
                "weight": 0.20,
                "penalty": round(0.20 * after_hours_ratio, 4),
                "health_contribution": round(0.20 * (1.0 - after_hours_ratio), 4),
            },
        }
    }
