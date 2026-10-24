"""
EngageIQ Data Pipeline - Pattern and Anomaly Detector
Detects organizational risk patterns:
1. collab-down-output-flat: Engagement/health drops while output stays flat (burnout risk)
2. both-layers-down: Both engagement and output decline
3. persistent-decline: Severe low score requiring intervention
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DetectedPattern:
    employee_id: str
    employee_name: str
    pattern_id: str
    severity: str  # low, medium, high, critical
    description: str
    evidence: Dict[str, Any]
    detected_at: datetime = datetime.utcnow()


class PatternDetector:
    """Analyzes calculated scores to detect meaningful risk patterns."""

    def detect_patterns(self, df) -> List[DetectedPattern]:
        """Detects patterns across employee rows."""
        events: List[DetectedPattern] = []

        for _, row in df.iterrows():
            emp_id = str(row.get("employee_id", ""))
            name = str(row.get("employee_name", emp_id))
            ehs = float(row.get("ehs_score", 0.7))
            opi = float(row.get("opi_score", 0.7))
            pace = float(row.get("pace_score", 0.7))
            risk = str(row.get("risk_category", "Healthy"))

            # Pattern 1: Collab Down, Output Flat (Classic Burnout / Friction Pattern)
            # High work output (OPI >= 0.70) but suffering work pattern health (EHS < 0.60)
            if ehs < 0.60 and opi >= 0.70:
                events.append(DetectedPattern(
                    employee_id=emp_id,
                    employee_name=name,
                    pattern_id="collab-down-output-flat",
                    severity="high" if ehs < 0.45 else "medium",
                    description=(
                        f"Work health is deteriorating (EHS {ehs:.2f}) while output remains high (OPI {opi:.2f}). "
                        f"Indicates hidden disengagement, meeting overload, or imminent burnout."
                    ),
                    evidence={
                        "ehs": ehs,
                        "opi": opi,
                        "pace": pace,
                        "meeting_load": float(row.get("meeting_load", 0.0)),
                        "after_hours_ratio": float(row.get("after_hours_ratio", 0.0))
                    }
                ))

            # Pattern 2: Both Layers Down
            elif ehs < 0.50 and opi < 0.50:
                events.append(DetectedPattern(
                    employee_id=emp_id,
                    employee_name=name,
                    pattern_id="both-layers-down",
                    severity="critical" if pace < 0.35 else "high",
                    description=(
                        f"Both work health (EHS {ehs:.2f}) and output delivery (OPI {opi:.2f}) are depressed. "
                        f"Active risk requiring supportive manager intervention."
                    ),
                    evidence={
                        "ehs": ehs,
                        "opi": opi,
                        "pace": pace,
                        "completion_rate": float(row.get("completion_rate", 0.0))
                    }
                ))

            # Pattern 3: Severe At-Risk
            elif risk == "At-Risk":
                events.append(DetectedPattern(
                    employee_id=emp_id,
                    employee_name=name,
                    pattern_id="persistent-decline",
                    severity="high",
                    description=f"PACE score ({pace:.2f}) has crossed below the At-Risk threshold (< 0.40).",
                    evidence={"ehs": ehs, "opi": opi, "pace": pace}
                ))

        return events
