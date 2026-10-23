"""
EngageIQ Data Pipeline - PACE Scoring Engine
Combines EHS and OPI using the 40:60 PACE formula:
    PACE = (0.40 * EHS) + (0.60 * OPI)
Classifies employees into risk bands: Healthy, Moderate, At-Risk.
"""

from typing import Dict, Any, Tuple
import pandas as pd
from .ehs_calculator import compute_ehs
from .opi_calculator import compute_opi


def compute_pace(ehs: float, opi: float, ehs_weight: float = 0.40, opi_weight: float = 0.60) -> float:
    """Combines EHS and OPI using the 40:60 formula."""
    pace = (ehs_weight * ehs) + (opi_weight * opi)
    return round(max(0.0, min(1.0, float(pace))), 4)


def classify_risk(pace_score: float, persistent_anomaly: bool = False) -> str:
    """
    Classifies PACE score into risk category:
    - Healthy: PACE >= 0.70
    - Moderate: 0.40 <= PACE < 0.70
    - At-Risk: PACE < 0.40
    """
    if pace_score >= 0.70:
        band = "Healthy"
    elif pace_score >= 0.40:
        band = "Moderate"
    else:
        band = "At-Risk"

    if persistent_anomaly and band != "At-Risk":
        band = "Moderate" if band == "Healthy" else "At-Risk"

    return band


class PACEEngine:
    """Full-featured scoring engine for processing employee rows and DataFrames."""

    def __init__(self, ehs_weight: float = 0.40, opi_weight: float = 0.60):
        self.ehs_weight = ehs_weight
        self.opi_weight = opi_weight

    def process_record(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates EHS, OPI, PACE, and Risk for a single record."""
        meeting_load = float(row.get("meeting_load", 0.4))
        focus_gap = float(row.get("focus_gap", 0.3))
        response_latency = float(row.get("response_latency", 0.25))
        after_hours_ratio = float(row.get("after_hours_ratio", 0.2))

        completion_rate = float(row.get("completion_rate", 0.8))
        velocity = float(row.get("velocity", 0.8))
        deadline_adherence = float(row.get("deadline_adherence", 0.85))
        code_activity = float(row.get("code_activity", 0.7))
        rework_ratio = float(row.get("rework_ratio", 0.1))

        ehs = compute_ehs(meeting_load, focus_gap, response_latency, after_hours_ratio)
        opi = compute_opi(completion_rate, velocity, deadline_adherence, code_activity, rework_ratio)
        pace = compute_pace(ehs, opi, self.ehs_weight, self.opi_weight)
        risk = classify_risk(pace)

        explanation = f"EHS: {ehs:.2f} (40%), OPI: {opi:.2f} (60%)"

        return {
            "ehs_score": ehs,
            "opi_score": opi,
            "pace_score": pace,
            "risk_category": risk,
            "risk_explanation": explanation
        }

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Processes an entire DataFrame and appends scoring columns."""
        df = df.copy()

        df["ehs_score"] = df.apply(
            lambda r: compute_ehs(
                float(r["meeting_load"]),
                float(r["focus_gap"]),
                float(r["response_latency"]),
                float(r["after_hours_ratio"])
            ),
            axis=1
        )

        df["opi_score"] = df.apply(
            lambda r: compute_opi(
                float(r["completion_rate"]),
                float(r["velocity"]),
                float(r["deadline_adherence"]),
                float(r["code_activity"]),
                float(r["rework_ratio"])
            ),
            axis=1
        )

        df["pace_score"] = df.apply(
            lambda r: compute_pace(r["ehs_score"], r["opi_score"], self.ehs_weight, self.opi_weight),
            axis=1
        )

        df["risk_category"] = df["pace_score"].apply(classify_risk)
        df["risk_explanation"] = df.apply(
            lambda r: f"EHS: {r['ehs_score']:.2f} (40%), OPI: {r['opi_score']:.2f} (60%)",
            axis=1
        )

        return df
