"""
Unit & Integration Tests for EngageIQ Data Integration Pipeline
Tests Identity Resolution, Noise Filtering, Multi-Source Aggregations, and Unified Schema Output.
"""

import pytest
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_ROOT))

from integration.identity_resolver import IdentityResolver, EmployeeIdentity
from integration.noise_filter import TimeZoneHelper, NoiseFilter
from integration.connectors.google_calendar import GoogleCalendarConnector
from integration.connectors.slack_connector import SlackConnector
from integration.connectors.jira_connector import JiraConnector
from integration.connectors.github_connector import GitHubConnector
from integration.metrics_aggregator import MetricsAggregator, AggregationPeriod


@pytest.fixture
def test_identity():
    return EmployeeIdentity(
        employee_id="EMP-9042",
        employee_name="Sarah Connor",
        role="Senior Backend Engineer",
        team_id="TEAM-ENG-03",
        team_name="Core Platform",
        email="sarah.connor@company.com",
        slack_user_id="U01928374",
        jira_account_id="5b10ac8d82e05b22cc7d4ef5",
        github_username="sconnor-dev",
        timezone="America/New_York",
        work_start_hour=9,
        work_end_hour=18
    )


# ─── 1. Identity Resolution Tests ──────────────────────────────────────────

def test_identity_resolution(test_identity):
    resolver = IdentityResolver()
    resolver.register_identity(test_identity)

    # Resolve via Slack
    resolved = resolver.resolve("slack", "U01928374")
    assert resolved is not None
    assert resolved.employee_id == "EMP-9042"

    # Resolve via GitHub
    resolved_git = resolver.resolve("github", "sconnor-dev")
    assert resolved_git.employee_name == "Sarah Connor"

    # Resolve via Jira
    resolved_jira = resolver.resolve("jira", "5b10ac8d82e05b22cc7d4ef5")
    assert resolved_jira.email == "sarah.connor@company.com"

    # Unknown identifier returns None
    assert resolver.resolve("slack", "U_UNKNOWN") is None


# ─── 2. Timezone & Noise Filter Tests ───────────────────────────────────────

def test_after_hours_detection():
    # 2:00 PM UTC = 10:00 AM New York (during work hours)
    ny_work_hour = datetime(2026, 10, 21, 14, 0, tzinfo=timezone.utc)
    assert not TimeZoneHelper.is_after_hours(ny_work_hour, tz_name="America/New_York", work_start_hour=9, work_end_hour=18)

    # 1:00 AM UTC = 9:00 PM New York (after hours)
    ny_after_hour = datetime(2026, 10, 21, 1, 0, tzinfo=timezone.utc)
    assert TimeZoneHelper.is_after_hours(ny_after_hour, tz_name="America/New_York", work_start_hour=9, work_end_hour=18)

    # Weekend (Sunday Oct 18, 2026)
    weekend_dt = datetime(2026, 10, 18, 15, 0, tzinfo=timezone.utc)
    assert TimeZoneHelper.is_after_hours(weekend_dt, tz_name="America/New_York")


def test_noise_filter():
    # Slack Bot message filtered
    assert not NoiseFilter.is_valid_slack_message({"bot_id": "B123", "text": "Deploy alert"})
    # Announcement channel filtered
    assert not NoiseFilter.is_valid_slack_message({"channel_name": "#announcements", "text": "All-hands today"})
    # Valid Slack message passes
    assert NoiseFilter.is_valid_slack_message({"user": "U123", "channel_name": "#eng-team", "text": "Review please"})

    # Dependabot commit filtered
    assert not NoiseFilter.is_valid_github_event({"author": "dependabot[bot]"})
    # Valid commit passes
    assert NoiseFilter.is_valid_github_event({"author": "sconnor-dev", "commit_message": "Fix race condition"})

    # Declined calendar event filtered
    declined_evt = {
        "attendees": [{"email": "user@test.com", "responseStatus": "declined"}]
    }
    assert not NoiseFilter.is_valid_calendar_event(declined_evt, "user@test.com")


# ─── 3. Google Calendar Connector Tests ────────────────────────────────────

def test_calendar_meeting_load_and_focus_gap():
    start_period = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    end_period = datetime(2026, 10, 23, 23, 59, tzinfo=timezone.utc)

    # 2 meetings of 1 hour each on Monday
    events = [
        {
            "id": "e1",
            "start": {"dateTime": "2026-10-19T14:00:00Z"},
            "end": {"dateTime": "2026-10-19T15:00:00Z"},
            "attendees": [{"email": "user@test.com", "responseStatus": "accepted"}]
        },
        {
            "id": "e2",
            "start": {"dateTime": "2026-10-19T16:00:00Z"},
            "end": {"dateTime": "2026-10-19T17:00:00Z"},
            "attendees": [{"email": "user@test.com", "responseStatus": "accepted"}]
        }
    ]

    res = GoogleCalendarConnector.process_calendar_events(
        events=events,
        employee_email="user@test.com",
        period_start_utc=start_period,
        period_end_utc=end_period,
        standard_work_hours=40.0
    )

    assert res["meeting_hours"] == 2.0
    assert res["meeting_load"] == pytest.approx(2.0 / 40.0, 0.01)
    assert res["focus_gap"] >= 0.0


# ─── 4. Slack Connector Tests ───────────────────────────────────────────────

def test_slack_response_latency():
    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 23, 23, 59, tzinfo=timezone.utc)

    messages = [
        # Mention arrived at 10:00
        {
            "ts": str(datetime(2026, 10, 19, 10, 0, tzinfo=timezone.utc).timestamp()),
            "user": "U_OTHER",
            "text": "Hello <@U01928374>",
            "channel": "C01",
            "thread_ts": "100.1"
        },
        # Reply by employee at 10:14 (14 mins later)
        {
            "ts": str(datetime(2026, 10, 19, 10, 14, tzinfo=timezone.utc).timestamp()),
            "user": "U01928374",
            "text": "Hey! Looking at it.",
            "channel": "C01",
            "thread_ts": "100.1"
        }
    ]

    res = SlackConnector.process_slack_events(messages, "U01928374", start, end)
    assert res["response_count"] == 1
    assert res["response_latency_minutes"] == pytest.approx(14.0, 0.1)


# ─── 5. Jira Connector Tests ────────────────────────────────────────────────

def test_jira_metrics():
    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 23, 23, 59, tzinfo=timezone.utc)

    issues = [
        {
            "fields": {
                "assignee": {"accountId": "ACC-1"},
                "status": {"name": "Done"},
                "resolutiondate": "2026-10-21T15:00:00.000+0000",
                "duedate": "2026-10-22",
                "customfield_10002": 5.0
            }
        },
        {
            "fields": {
                "assignee": {"accountId": "ACC-1"},
                "status": {"name": "In Progress"},
                "resolutiondate": None,
                "duedate": "2026-10-23",
                "customfield_10002": 3.0
            }
        }
    ]

    res = JiraConnector.process_jira_issues(issues, "ACC-1", start, end)
    assert res["assigned_count"] == 2
    assert res["total_completed_count"] == 1
    assert res["completion_rate"] == 0.50
    assert res["velocity"] == 5.0
    assert res["deadline_adherence"] == 1.0


# ─── 6. GitHub Connector Tests ──────────────────────────────────────────────

def test_github_code_activity():
    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 23, 23, 59, tzinfo=timezone.utc)

    commits = [
        {"author": {"login": "octo"}, "created_at": "2026-10-20T10:00:00Z", "commit": {"message": "feat: test"}},
        {"author": {"login": "octo"}, "created_at": "2026-10-20T11:00:00Z", "commit": {"message": "fix: bug"}}
    ]
    pulls = [
        {"user": {"login": "octo"}, "created_at": "2026-10-21T10:00:00Z"}
    ]
    reviews = [
        {"user": {"login": "octo"}, "submitted_at": "2026-10-22T10:00:00Z"}
    ]

    # Weighted: 1.0*2 commits + 3.0*1 PR + 2.0*1 Review = 2 + 3 + 2 = 7.0
    res = GitHubConnector.process_github_data(commits, pulls, reviews, "octo", start, end)
    assert res["commit_count"] == 2
    assert res["prs_opened"] == 1
    assert res["pr_reviews"] == 1
    assert res["code_activity"] == 7.0


# ─── 7. Unified Aggregator Output Schema Test ───────────────────────────────

def test_unified_metrics_aggregator(test_identity):
    resolver = IdentityResolver()
    resolver.register_identity(test_identity)
    aggregator = MetricsAggregator(resolver)

    start = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 23, 23, 59, 59, tzinfo=timezone.utc)
    period = AggregationPeriod(start_utc=start, end_utc=end)

    output = aggregator.aggregate_for_employee(
        employee_id="EMP-9042",
        period=period
    )

    out_dict = output.to_dict()
    assert out_dict["employee_id"] == "EMP-9042"
    assert out_dict["employee_name"] == "Sarah Connor"
    assert out_dict["role"] == "Senior Backend Engineer"
    assert out_dict["team_id"] == "TEAM-ENG-03"
    assert out_dict["team_name"] == "Core Platform"

    m = out_dict["metrics"]
    required_metric_fields = [
        "meeting_load", "focus_gap", "response_latency_minutes",
        "after_hours_ratio", "completion_rate", "velocity",
        "deadline_adherence", "code_activity", "rework_ratio"
    ]
    for field in required_metric_fields:
        assert field in m, f"Missing metric field: {field}"
