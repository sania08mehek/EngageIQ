"""
Tests for EHS, OPI, and 40:60 PACE Scoring
"""

import pytest
import sys
from pathlib import Path

# Add pipeline root to path
PIPELINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_ROOT))

from scoring.ehs_calculator import compute_ehs, compute_ehs_breakdown
from scoring.opi_calculator import compute_opi, compute_opi_breakdown
from scoring.pace_engine import compute_pace, classify_risk, PACEEngine


def test_ehs_optimal():
    """Zero load should yield 1.0 (optimal health)."""
    score = compute_ehs(meeting_load=0.0, focus_gap=0.0, response_latency=0.0, after_hours_ratio=0.0)
    assert score == 1.0


def test_ehs_overload():
    """Max load should yield 0.0."""
    score = compute_ehs(meeting_load=1.0, focus_gap=1.0, response_latency=1.0, after_hours_ratio=1.0)
    assert score == 0.0


def test_opi_calculation():
    """Verify OPI linear formula."""
    # 0.25*1.0 + 0.25*1.0 + 0.20*1.0 + 0.20*1.0 - 0.10*0.0 = 0.90
    score = compute_opi(completion_rate=1.0, velocity=1.0, deadline_adherence=1.0, code_activity=1.0, rework_ratio=0.0)
    assert score == 0.90


def test_pace_40_60_formula():
    """Verify (0.40 * EHS) + (0.60 * OPI)."""
    ehs = 0.80
    opi = 0.70
    expected = (0.40 * 0.80) + (0.60 * 0.70)  # 0.32 + 0.42 = 0.74
    score = compute_pace(ehs, opi)
    assert score == pytest.approx(expected, 0.001)


def test_risk_classification():
    assert classify_risk(0.75) == "Healthy"
    assert classify_risk(0.70) == "Healthy"
    assert classify_risk(0.69) == "Moderate"
    assert classify_risk(0.40) == "Moderate"
    assert classify_risk(0.39) == "At-Risk"
    assert classify_risk(0.20) == "At-Risk"
