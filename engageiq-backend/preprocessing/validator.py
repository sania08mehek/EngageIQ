"""
EngageIQ Data Pipeline - Data Validator
Validates incoming CSV rows against required columns, schema types, and metric value bounds.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    is_valid: bool
    total_records: int
    valid_records: int
    invalid_records: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DataValidator:
    """Validates employee input datasets for the EngageIQ data pipeline."""

    REQUIRED_IDENTIFIERS = ["employee_id", "employee_name"]
    
    # Normalized [0, 1] columns required by scoring engine
    SCORING_COLUMNS = [
        "meeting_load", "focus_gap", "response_latency", "after_hours_ratio",
        "completion_rate", "velocity", "deadline_adherence", "code_activity", "rework_ratio"
    ]
    
    # Raw alternative columns if pre-normalized are not supplied
    RAW_SIGNAL_COLUMNS = [
        "meeting_hours", "focus_gap_days", "response_latency_hours", "after_hours_pct"
    ]

    def __init__(self, strict_bounds: bool = False):
        self.strict_bounds = strict_bounds

    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, ValidationResult]:
        """
        Validates the input DataFrame.
        
        Returns:
            (valid_df, invalid_df, validation_result)
        """
        errors = []
        warnings = []
        total_records = len(df)
        
        if total_records == 0:
            return df, df, ValidationResult(
                is_valid=False,
                total_records=0,
                valid_records=0,
                invalid_records=0,
                errors=[{"row": 0, "message": "Uploaded dataset is empty"}]
            )

        # 1. Check required identifier columns
        missing_identifiers = [col for col in self.REQUIRED_IDENTIFIERS if col not in df.columns]
        if missing_identifiers:
            errors.append({
                "row": 0,
                "field": "columns",
                "message": f"Missing required identifier columns: {missing_identifiers}"
            })
            return df.iloc[0:0], df, ValidationResult(
                is_valid=False,
                total_records=total_records,
                valid_records=0,
                invalid_records=total_records,
                errors=errors
            )

        # 2. Check metric columns availability
        has_scoring_cols = all(col in df.columns for col in self.SCORING_COLUMNS)
        has_raw_cols = all(col in df.columns for col in self.RAW_SIGNAL_COLUMNS)
        
        if not has_scoring_cols and not has_raw_cols:
            errors.append({
                "row": 0,
                "field": "columns",
                "message": f"Dataset must contain either normalized columns {self.SCORING_COLUMNS} or raw columns {self.RAW_SIGNAL_COLUMNS}"
            })
            return df.iloc[0:0], df, ValidationResult(
                is_valid=False,
                total_records=total_records,
                valid_records=0,
                invalid_records=total_records,
                errors=errors
            )

        # 3. Row-by-row validation
        invalid_row_indices = set()
        
        # Check duplicate employee_ids
        duplicate_ids = df[df["employee_id"].duplicated(keep=False)]["employee_id"].tolist()
        if duplicate_ids:
            warnings.append(f"Found {len(duplicate_ids)} rows with duplicate employee_id: {set(duplicate_ids)}")

        # Check column types and ranges
        for idx, row in df.iterrows():
            row_num = int(idx) + 1
            
            # Check ID and Name not empty
            if pd.isna(row.get("employee_id")) or str(row.get("employee_id")).strip() == "":
                invalid_row_indices.add(idx)
                errors.append({"row": row_num, "field": "employee_id", "message": "Employee ID cannot be empty"})
                continue
                
            if pd.isna(row.get("employee_name")) or str(row.get("employee_name")).strip() == "":
                invalid_row_indices.add(idx)
                errors.append({"row": row_num, "field": "employee_name", "message": "Employee Name cannot be empty"})
                continue

            # Check numeric columns if present
            for col in self.SCORING_COLUMNS:
                if col in df.columns and pd.notna(row.get(col)):
                    try:
                        val = float(row[col])
                        if val < 0.0 or val > 1.5:  # Allow slight velocity overflow (e.g. 1.2 for 120%)
                            if self.strict_bounds and (val < 0.0 or val > 1.0):
                                invalid_row_indices.add(idx)
                                errors.append({"row": row_num, "field": col, "message": f"Value {val} out of bounds [0, 1]"})
                            elif val < 0.0:
                                invalid_row_indices.add(idx)
                                errors.append({"row": row_num, "field": col, "message": f"Negative value {val} not allowed"})
                    except (ValueError, TypeError):
                        invalid_row_indices.add(idx)
                        errors.append({"row": row_num, "field": col, "message": f"Non-numeric value: {row[col]}"})

        valid_mask = ~df.index.isin(invalid_row_indices)
        valid_df = df[valid_mask].copy().reset_index(drop=True)
        invalid_df = df[~valid_mask].copy().reset_index(drop=True)
        
        result = ValidationResult(
            is_valid=len(invalid_df) == 0,
            total_records=total_records,
            valid_records=len(valid_df),
            invalid_records=len(invalid_df),
            errors=errors,
            warnings=warnings
        )
        
        return valid_df, invalid_df, result
