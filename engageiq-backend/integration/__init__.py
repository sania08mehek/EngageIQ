"""
EngageIQ Data Integration Pipeline Package
Extracts, resolves identities, filters noise, and computes Pace Score metrics
from Google Calendar, Slack, Jira, and GitHub.
"""

from .identity_resolver import IdentityResolver, EmployeeIdentity
from .noise_filter import NoiseFilter, TimeZoneHelper
from .metrics_aggregator import MetricsAggregator, AggregationPeriod, UnifiedMetricOutput

__all__ = [
    "IdentityResolver",
    "EmployeeIdentity",
    "NoiseFilter",
    "TimeZoneHelper",
    "MetricsAggregator",
    "AggregationPeriod",
    "UnifiedMetricOutput",
]
