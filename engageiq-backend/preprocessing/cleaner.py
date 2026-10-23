"""
EngageIQ Data Pipeline - Data Cleaner
Handles string trimming, casing standardization, imputation for missing values,
and default role/team assignments.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


class DataCleaner:
    """Cleans and imputes missing or inconsistent data in employee records."""

    DEFAULT_ROLE = "Engineer"
    DEFAULT_TEAM_ID = "platform"
    DEFAULT_TEAM_NAME = "Platform Engineering"

    VALID_ROLES = {
        "engineer": "Engineer",
        "designer": "Designer",
        "salesperson": "Salesperson",
        "sales": "Salesperson",
        "manager": "Manager",
        "lead": "Manager",
        "product manager": "Manager",
        "analyst": "Engineer"
    }

    # Sensible median defaults for scoring columns if missing
    DEFAULT_METRIC_VALUES = {
        "meeting_load": 0.40,
        "focus_gap": 0.30,
        "response_latency": 0.25,
        "after_hours_ratio": 0.20,
        "completion_rate": 0.80,
        "velocity": 0.80,
        "deadline_adherence": 0.85,
        "code_activity": 0.70,
        "rework_ratio": 0.10,
        "meeting_hours": 12.0,
        "focus_gap_days": 1.5,
        "response_latency_hours": 3.0,
        "after_hours_pct": 10.0,
    }

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans a validated DataFrame:
        - Strips whitespace
        - Standardizes roles and team names
        - Imputes missing numeric values
        """
        df = df.copy()

        # 1. Clean string identifier columns
        for col in ["employee_id", "employee_name", "role", "team_id", "team_name"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace 'nan', 'None' with actual None
                df[col] = df[col].replace(["nan", "None", "", "NaN"], None)

        # 2. Standardize Role
        if "role" not in df.columns or df["role"].isna().all():
            df["role"] = self.DEFAULT_ROLE
        else:
            df["role"] = df["role"].apply(self._standardize_role)

        # 3. Standardize Team ID & Team Name
        if "team_id" not in df.columns or df["team_id"].isna().all():
            df["team_id"] = self.DEFAULT_TEAM_ID
        else:
            df["team_id"] = df["team_id"].fillna(self.DEFAULT_TEAM_ID)

        if "team_name" not in df.columns:
            # Map team_id to friendly name
            team_names = {
                "platform": "Platform Engineering",
                "design": "Product Design",
                "sales": "Enterprise Sales",
                "data-ml": "Data & Machine Learning",
                "marketing": "Growth Marketing",
                "support": "Customer Support",
                "core": "Core Backend",
            }
            df["team_name"] = df["team_id"].map(lambda tid: team_names.get(str(tid).lower(), str(tid).title()))
        else:
            df["team_name"] = df["team_name"].fillna(self.DEFAULT_TEAM_NAME)

        # 4. Impute missing numeric values using role-specific medians or defaults
        numeric_cols = [
            "meeting_load", "focus_gap", "response_latency", "after_hours_ratio",
            "completion_rate", "velocity", "deadline_adherence", "code_activity", "rework_ratio",
            "meeting_hours", "focus_gap_days", "response_latency_hours", "after_hours_pct"
        ]

        for col in numeric_cols:
            if col in df.columns:
                # Convert to numeric
                df[col] = pd.to_numeric(df[col], errors="coerce")
                
                # Role-specific median imputation
                if df[col].isna().any():
                    role_medians = df.groupby("role")[col].transform("median")
                    df[col] = df[col].fillna(role_medians)
                    
                    # Fallback to general default
                    default_val = self.DEFAULT_METRIC_VALUES.get(col, 0.5)
                    df[col] = df[col].fillna(default_val)

        return df

    def _standardize_role(self, role_str: Any) -> str:
        if not role_str or pd.isna(role_str):
            return self.DEFAULT_ROLE
        clean_key = str(role_str).strip().lower()
        return self.VALID_ROLES.get(clean_key, str(role_str).strip().title())
