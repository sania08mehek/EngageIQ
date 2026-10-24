"""
EngageIQ Data Pipeline - Role-Aware Normalizer
Normalizes raw work signals and output features into standardized [0, 1] scales
taking the employee's role into account.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class RoleAwareNormalizer:
    """
    Applies role-aware normalization profiles.
    
    Different job roles have different baseline expectations:
    - Managers naturally spend more hours in meetings than Engineers.
    - Salespeople must respond faster to inbound communications than Engineers in deep focus.
    - Engineers require larger uninterrupted focus blocks.
    """

    # Role-specific baseline configuration
    ROLE_PROFILES = {
        "Engineer": {
            "max_meeting_hours": 24.0,       # Meetings above 24h = full load (1.0)
            "max_focus_gap_days": 5.0,
            "max_latency_hours": 12.0,       # Max latency tolerance
            "max_after_hours_pct": 30.0,
            "target_velocity": 1.0,
            "max_rework_pct": 35.0,
        },
        "Designer": {
            "max_meeting_hours": 20.0,
            "max_focus_gap_days": 4.5,
            "max_latency_hours": 10.0,
            "max_after_hours_pct": 30.0,
            "target_velocity": 1.0,
            "max_rework_pct": 40.0,          # Design iterations naturally have higher revision rate
        },
        "Salesperson": {
            "max_meeting_hours": 30.0,       # Client meetings are expected
            "max_focus_gap_days": 5.0,
            "max_latency_hours": 6.0,        # Sales demands high responsiveness
            "max_after_hours_pct": 35.0,
            "target_velocity": 1.0,
            "max_rework_pct": 25.0,
        },
        "Manager": {
            "max_meeting_hours": 34.0,       # Meetings are primary managerial work
            "max_focus_gap_days": 5.0,
            "max_latency_hours": 8.0,
            "max_after_hours_pct": 35.0,
            "target_velocity": 1.0,
            "max_rework_pct": 30.0,
        },
        "Default": {
            "max_meeting_hours": 24.0,
            "max_focus_gap_days": 5.0,
            "max_latency_hours": 12.0,
            "max_after_hours_pct": 30.0,
            "target_velocity": 1.0,
            "max_rework_pct": 30.0,
        }
    }

    def normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizes a cleaned DataFrame.
        If raw columns (meeting_hours, etc.) are present, computes normalized columns.
        Ensures all scoring columns are clipped to valid [0, 1] ranges.
        """
        df = df.copy()

        # If raw signal columns exist, compute role-aware normalized metrics
        has_raw_signals = all(col in df.columns for col in [
            "meeting_hours", "focus_gap_days", "response_latency_hours", "after_hours_pct"
        ])

        if has_raw_signals:
            df["meeting_load"] = df.apply(self._normalize_meeting_load, axis=1)
            df["focus_gap"] = df.apply(self._normalize_focus_gap, axis=1)
            df["response_latency"] = df.apply(self._normalize_response_latency, axis=1)
            df["after_hours_ratio"] = df.apply(self._normalize_after_hours, axis=1)

        # Ensure all standard scoring columns exist and are strictly clipped [0, 1]
        for col in ["meeting_load", "focus_gap", "response_latency", "after_hours_ratio"]:
            if col in df.columns:
                df[col] = df[col].clip(0.0, 1.0).round(4)

        for col in ["completion_rate", "deadline_adherence", "code_activity", "rework_ratio"]:
            if col in df.columns:
                df[col] = df[col].clip(0.0, 1.0).round(4)

        if "velocity" in df.columns:
            # Velocity can reach 1.25 (125% of sprint target) but clip between 0 and 1.5
            df["velocity"] = df["velocity"].clip(0.0, 1.5).round(4)

        return df

    def _get_profile(self, role: Any) -> Dict[str, float]:
        clean_role = str(role).strip().title() if role else "Default"
        return self.ROLE_PROFILES.get(clean_role, self.ROLE_PROFILES["Default"])

    def _normalize_meeting_load(self, row: pd.Series) -> float:
        profile = self._get_profile(row.get("role"))
        raw_hours = float(row.get("meeting_hours", 12.0))
        # 0 hours = 0.0 load; max_hours = 1.0 load
        return round(float(np.clip(raw_hours / profile["max_meeting_hours"], 0.0, 1.0)), 4)

    def _normalize_focus_gap(self, row: pd.Series) -> float:
        profile = self._get_profile(row.get("role"))
        raw_days = float(row.get("focus_gap_days", 1.5))
        return round(float(np.clip(raw_days / profile["max_focus_gap_days"], 0.0, 1.0)), 4)

    def _normalize_response_latency(self, row: pd.Series) -> float:
        profile = self._get_profile(row.get("role"))
        raw_latency = float(row.get("response_latency_hours", 3.0))
        return round(float(np.clip(raw_latency / profile["max_latency_hours"], 0.0, 1.0)), 4)

    def _normalize_after_hours(self, row: pd.Series) -> float:
        profile = self._get_profile(row.get("role"))
        raw_pct = float(row.get("after_hours_pct", 10.0))
        return round(float(np.clip(raw_pct / profile["max_after_hours_pct"], 0.0, 1.0)), 4)
