"""
EngageIQ Data Integration Pipeline - Step 3 & 5: Metrics Aggregator & Graceful Degradation
Combines extracted data from Google Calendar, Slack, Jira, and GitHub into the Standardized Unified Schema.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from integration.identity_resolver import EmployeeIdentity, identity_resolver
from integration.noise_filter import TimeZoneHelper
from integration.connectors.google_calendar import GoogleCalendarConnector
from integration.connectors.slack_connector import SlackConnector
from integration.connectors.jira_connector import JiraConnector
from integration.connectors.github_connector import GitHubConnector


@dataclass
class AggregationPeriod:
    start_utc: datetime
    end_utc: datetime


@dataclass
class UnifiedMetricOutput:
    employee_id: str
    employee_name: str
    role: str
    team_id: str
    team_name: str
    period_start: str
    period_end: str
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsAggregator:
    """
    Transforms multi-source raw API streams into unified employee engagement and output metrics.
    Handles missing accounts, alternatives, and role-based graceful degradation.
    """

    def __init__(self, resolver=None):
        self.resolver = resolver or identity_resolver

    def aggregate_for_employee(
        self,
        employee_id: str,
        period: AggregationPeriod,
        calendar_events: Optional[List[Dict[str, Any]]] = None,
        slack_messages: Optional[List[Dict[str, Any]]] = None,
        jira_issues: Optional[List[Dict[str, Any]]] = None,
        github_data: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> UnifiedMetricOutput:
        """
        Executes end-to-end metric computation for a single employee over an aggregation window.
        """
        identity = self.resolver.get_by_employee_id(employee_id)
        if not identity:
            raise ValueError(f"Unknown employee_id: {employee_id}")

        all_activity_timestamps: List[datetime] = []

        # ─── 1. Google Calendar Metrics (meeting_load, focus_gap) ────────────
        cal_res = {"meeting_load": 0.25, "focus_gap": 2.0}
        if calendar_events:
            cal_res = GoogleCalendarConnector.process_calendar_events(
                events=calendar_events,
                employee_email=identity.email,
                period_start_utc=period.start_utc,
                period_end_utc=period.end_utc,
                tz_name=identity.timezone,
                work_start_hour=identity.work_start_hour,
                work_end_hour=identity.work_end_hour
            )

        # ─── 2. Slack Metrics (response_latency, activity timestamps) ────────
        slack_res = {"response_latency_minutes": 15.0, "activity_timestamps": []}
        if slack_messages and identity.slack_user_id:
            slack_res = SlackConnector.process_slack_events(
                messages=slack_messages,
                slack_user_id=identity.slack_user_id,
                period_start_utc=period.start_utc,
                period_end_utc=period.end_utc
            )
            all_activity_timestamps.extend(slack_res.get("activity_timestamps", []))
        else:
            # Fallback / Graceful degradation for response latency
            # If user has no Slack, substitute role-based baseline
            slack_res["response_latency_minutes"] = 12.0 if "Sales" in identity.role else 18.0

        # ─── 3. Jira Metrics (completion_rate, velocity, deadline_adherence) ──
        jira_res = {
            "completion_rate": 0.88,
            "velocity": 12.0,
            "deadline_adherence": 0.92,
            "reopened_tickets_count": 0,
            "total_completed_count": 8,
            "activity_timestamps": []
        }
        if jira_issues and identity.jira_account_id:
            jira_res = JiraConnector.process_jira_issues(
                issues=jira_issues,
                jira_account_id=identity.jira_account_id,
                period_start_utc=period.start_utc,
                period_end_utc=period.end_utc
            )
            all_activity_timestamps.extend(jira_res.get("activity_timestamps", []))

        # ─── 4. GitHub Metrics (code_activity, reverted commits) ─────────────
        # Graceful degradation: Check if GitHub handle exists
        has_github = bool(identity.github_username and github_data)
        git_res = {
            "code_activity": 0.0,
            "reverted_commits": 0,
            "activity_timestamps": []
        }
        
        if has_github:
            git_res = GitHubConnector.process_github_data(
                commits=github_data.get("commits", []),
                pulls=github_data.get("pulls", []),
                reviews=github_data.get("reviews", []),
                github_username=identity.github_username,
                period_start_utc=period.start_utc,
                period_end_utc=period.end_utc
            )
            all_activity_timestamps.extend(git_res.get("activity_timestamps", []))
        else:
            # Edge case handling: If GitHub is not linked (e.g. Designer or Sales),
            # fall back to Jira engineering throughput or task activity
            if "Engineer" in identity.role:
                # Engineer missing GitHub handle -> estimate code activity from Jira velocity
                git_res["code_activity"] = round(jira_res.get("velocity", 10.0) * 5.0, 1)
            else:
                # Non-engineers: assign role-appropriate activity index
                git_res["code_activity"] = 75.0

        # ─── 5. Multi-Source after_hours_ratio ──────────────────────────────
        # Formula: (Activity events logged outside work hours) / (Total activity events)
        after_hours_ratio = 0.08  # default baseline if no active events in window
        if all_activity_timestamps:
            after_hours_count = 0
            for ts in all_activity_timestamps:
                if TimeZoneHelper.is_after_hours(
                    utc_dt=ts,
                    tz_name=identity.timezone,
                    work_start_hour=identity.work_start_hour,
                    work_end_hour=identity.work_end_hour,
                    work_days=identity.work_days
                ):
                    after_hours_count += 1
            after_hours_ratio = round(after_hours_count / len(all_activity_timestamps), 4)

        # ─── 6. Multi-Source rework_ratio ───────────────────────────────────
        # Formula: (Reopened tickets + Reverted commits) / (Total completed work items)
        reopened_jira = jira_res.get("reopened_tickets_count", 0)
        reverted_git = git_res.get("reverted_commits", 0)
        total_items = max(1, jira_res.get("total_completed_count", 0) + git_res.get("prs_opened", 0))
        
        rework_ratio = round((reopened_jira + reverted_git) / total_items, 4)
        rework_ratio = min(0.50, max(0.01, rework_ratio))

        # ─── 7. Assemble Standardized Unified Output Record ─────────────────
        final_metrics = {
            "meeting_load": round(cal_res["meeting_load"], 2),
            "focus_gap": round(cal_res["focus_gap"], 1),
            "response_latency_minutes": round(slack_res["response_latency_minutes"], 1),
            "after_hours_ratio": round(after_hours_ratio, 2),
            "completion_rate": round(jira_res["completion_rate"], 2),
            "velocity": round(jira_res["velocity"], 1),
            "deadline_adherence": round(jira_res["deadline_adherence"], 2),
            "code_activity": round(git_res["code_activity"], 1),
            "rework_ratio": round(rework_ratio, 2),
        }

        return UnifiedMetricOutput(
            employee_id=identity.employee_id,
            employee_name=identity.employee_name,
            role=identity.role,
            team_id=identity.team_id,
            team_name=identity.team_name,
            period_start=period.start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            period_end=period.end_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            metrics=final_metrics
        )
