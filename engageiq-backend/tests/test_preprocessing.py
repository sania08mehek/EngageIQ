"""
Tests for Data Preprocessing (Validator, Cleaner, Normalizer)
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add pipeline root to path
PIPELINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_ROOT))

from preprocessing.validator import DataValidator
from preprocessing.cleaner import DataCleaner
from preprocessing.normalizer import RoleAwareNormalizer


@pytest.fixture
def sample_raw_df():
    return pd.DataFrame({
        "employee_id": ["E01", "E02", "E03"],
        "employee_name": ["Alice Chen", "Bob Smith", "Charlie Day"],
        "role": ["engineer", "sales", "manager"],
        "team_id": ["platform", "sales", "core"],
        "meeting_load": [0.2, 0.4, 0.6],
        "focus_gap": [0.1, 0.3, 0.5],
        "response_latency": [0.1, 0.2, 0.3],
        "after_hours_ratio": [0.05, 0.15, 0.25],
        "completion_rate": [0.95, 0.85, 0.75],
        "velocity": [1.0, 0.9, 0.8],
        "deadline_adherence": [0.98, 0.90, 0.80],
        "code_activity": [0.85, 0.70, 0.60],
        "rework_ratio": [0.05, 0.10, 0.15],
    })


def test_validator_success(sample_raw_df):
    validator = DataValidator()
    valid_df, invalid_df, res = validator.validate_dataframe(sample_raw_df)
    assert res.is_valid is True
    assert len(valid_df) == 3
    assert len(invalid_df) == 0


def test_validator_missing_id(sample_raw_df):
    sample_raw_df.loc[0, "employee_id"] = None
    validator = DataValidator()
    valid_df, invalid_df, res = validator.validate_dataframe(sample_raw_df)
    assert len(invalid_df) == 1
    assert len(valid_df) == 2


def test_cleaner_roles(sample_raw_df):
    cleaner = DataCleaner()
    cleaned = cleaner.clean_dataframe(sample_raw_df)
    assert cleaned.loc[0, "role"] == "Engineer"
    assert cleaned.loc[1, "role"] == "Salesperson"
    assert cleaned.loc[2, "role"] == "Manager"


def test_normalizer_bounds(sample_raw_df):
    cleaner = DataCleaner()
    normalizer = RoleAwareNormalizer()
    cleaned = cleaner.clean_dataframe(sample_raw_df)
    normalized = normalizer.normalize_dataframe(cleaned)

    for col in ["meeting_load", "focus_gap", "response_latency", "after_hours_ratio"]:
        assert (normalized[col] >= 0.0).all()
        assert (normalized[col] <= 1.0).all()
