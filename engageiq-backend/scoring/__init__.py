"""
EngageIQ Data Pipeline - Scoring Package
EHS, OPI, and 40:60 PACE engine with pattern detection.
"""

from .ehs_calculator import compute_ehs, compute_ehs_breakdown
from .opi_calculator import compute_opi, compute_opi_breakdown
from .pace_engine import compute_pace, classify_risk, PACEEngine
from .pattern_detector import PatternDetector, DetectedPattern

__all__ = [
    "compute_ehs", "compute_ehs_breakdown",
    "compute_opi", "compute_opi_breakdown",
    "compute_pace", "classify_risk", "PACEEngine",
    "PatternDetector", "DetectedPattern"
]
