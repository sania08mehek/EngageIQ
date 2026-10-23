"""
EngageIQ Data Integration - Synthetic Raw Events Generator
Generates realistic raw API payloads for Google Calendar, Slack, Jira, and GitHub
for testing, backfilling, and continuous pipeline execution.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from integration.identity_resolver import EmployeeIdentity, identity_resolver


class SyntheticRawEventsGenerator:
    """Generates authentic API payloads mimicking GitHub, Slack, Jira, and Calendar."""

    @staticmethod
    def generate_events_for_employee(
        identity: EmployeeIdentity,
        period_start: datetime,
        period_end: datetime,
        profile: str = "healthy"  # 'healthy', 'overloaded', 'at_risk'
    ) -> Dict[str, Any]:
        """
        Creates synthetic multi-platform raw data for an employee.
        """
        cal_events = SyntheticRawEventsGenerator._generate_calendar_events(identity, period_start, period_end, profile)
        slack_msgs = SyntheticRawEventsGenerator._generate_slack_messages(identity, period_start, period_end, profile)
        jira_issues = SyntheticRawEventsGenerator._generate_jira_issues(identity, period_start, period_end, profile)
        github_data = SyntheticRawEventsGenerator._generate_github_data(identity, period_start, period_end, profile)

        return {
            "employee_id": identity.employee_id,
            "calendar_events": cal_events,
            "slack_messages": slack_msgs,
            "jira_issues": jira_issues,
            "github_data": github_data
        }

    @staticmethod
    def _generate_calendar_events(identity: EmployeeIdentity, start: datetime, end: datetime, profile: str) -> List[Dict]:
        events = []
        num_meetings = 18 if profile == "overloaded" else 10 if profile == "healthy" else 22
        
        # 1. Regular accepted meetings
        curr = start
        while curr < end and len(events) < num_meetings:
            hour = random.choice([10, 11, 14, 15, 16])
            duration_minutes = random.choice([30, 45, 60])
            meeting_start = curr.replace(hour=hour, minute=0, second=0)
            meeting_end = meeting_start + timedelta(minutes=duration_minutes)

            events.append({
                "id": f"cal-{random.randint(1000, 9999)}",
                "summary": random.choice(["Sprint Planning", "1:1 Sync", "Architecture Review", "Customer Demo"]),
                "start": {"dateTime": meeting_start.isoformat()},
                "end": {"dateTime": meeting_end.isoformat()},
                "attendees": [
                    {"email": identity.email, "responseStatus": "accepted"},
                    {"email": "colleague@company.com", "responseStatus": "accepted"}
                ]
            })
            curr += timedelta(days=1)

        # 2. Add an all-day event (which should be filtered out by NoiseFilter)
        events.append({
            "id": "cal-allday-1",
            "summary": "Company Holiday",
            "start": {"date": start.strftime("%Y-%m-%d")},
            "end": {"date": (start + timedelta(days=1)).strftime("%Y-%m-%d")},
            "attendees": [{"email": identity.email, "responseStatus": "accepted"}]
        })

        # 3. Add a declined event (which should be filtered out)
        events.append({
            "id": "cal-declined-1",
            "summary": "Optional Brownbag",
            "start": {"dateTime": (start + timedelta(days=2, hours=12)).isoformat()},
            "end": {"dateTime": (start + timedelta(days=2, hours=13)).isoformat()},
            "attendees": [{"email": identity.email, "responseStatus": "declined"}]
        })

        return events

    @staticmethod
    def _generate_slack_messages(identity: EmployeeIdentity, start: datetime, end: datetime, profile: str) -> List[Dict]:
        messages = []
        uid = identity.slack_user_id or "U_DEFAULT"
        latency_target_mins = 8.0 if profile == "healthy" else 35.0

        for day_offset in range(5):
            day_base = start + timedelta(days=day_offset, hours=10)
            
            # Incoming mention
            mention_ts = day_base
            messages.append({
                "ts": str(mention_ts.timestamp()),
                "user": "U99998888",
                "text": f"Hey <@{uid}> can you check this pull request?",
                "channel": "C01_PROJECT",
                "channel_type": "channel",
                "thread_ts": str(mention_ts.timestamp())
            })

            # Employee reply after latency
            reply_ts = mention_ts + timedelta(minutes=latency_target_mins + random.uniform(-2, 5))
            messages.append({
                "ts": str(reply_ts.timestamp()),
                "user": uid,
                "text": "Sure, taking a look right now!",
                "channel": "C01_PROJECT",
                "channel_type": "channel",
                "thread_ts": str(mention_ts.timestamp())
            })

        # Bot message (should be filtered)
        messages.append({
            "ts": str((start + timedelta(hours=5)).timestamp()),
            "user": "UBOT123",
            "bot_id": "B12345",
            "subtype": "bot_message",
            "text": "Automated deployment finished successfully.",
            "channel": "C01_PROJECT"
        })

        return messages

    @staticmethod
    def _generate_jira_issues(identity: EmployeeIdentity, start: datetime, end: datetime, profile: str) -> List[Dict]:
        issues = []
        acc_id = identity.jira_account_id or "ACC_DEFAULT"
        total = 8 if profile == "healthy" else 6

        for i in range(1, total + 1):
            resolution_dt = start + timedelta(days=i * 0.5 + 1)
            due_dt = resolution_dt + timedelta(days=1)  # on-time

            issue_dict = {
                "id": f"JIRA-{100 + i}",
                "key": f"ENG-{100 + i}",
                "fields": {
                    "assignee": {"accountId": acc_id},
                    "status": {"name": "Done"},
                    "resolutiondate": resolution_dt.isoformat(),
                    "duedate": due_dt.strftime("%Y-%m-%d"),
                    "updated": resolution_dt.isoformat(),
                    "customfield_10002": random.choice([2.0, 3.0, 5.0])
                },
                "changelog": {
                    "histories": []
                }
            }

            # If overloaded or at-risk, inject a ticket reopen in changelog
            if i == 1 and profile in ("overloaded", "at_risk"):
                issue_dict["changelog"]["histories"].append({
                    "created": (start + timedelta(days=2)).isoformat(),
                    "items": [
                        {"field": "status", "fromString": "Done", "toString": "In Progress"}
                    ]
                })

            issues.append(issue_dict)

        return issues

    @staticmethod
    def _generate_github_data(identity: EmployeeIdentity, start: datetime, end: datetime, profile: str) -> Dict:
        if not identity.github_username:
            return {"commits": [], "pulls": [], "reviews": []}

        user = identity.github_username
        commits = []
        pulls = []
        reviews = []

        num_commits = 16 if profile == "healthy" else 8
        for i in range(num_commits):
            c_time = start + timedelta(days=random.uniform(0.5, 4.5), hours=random.choice([10, 14, 16]))
            msg = f"Feat: implement module component {i}"
            if i == 0 and profile == "at_risk":
                msg = f"Revert 'bad regression fix in component {i}'"

            commits.append({
                "author": {"login": user},
                "commit": {
                    "author": {"name": user, "date": c_time.isoformat()},
                    "message": msg
                }
            })

        # Add 1 PR and 2 PR reviews
        pulls.append({
            "user": {"login": user},
            "created_at": (start + timedelta(days=1, hours=11)).isoformat(),
            "title": "Add async processing pipeline"
        })

        reviews.append({
            "user": {"login": user},
            "submitted_at": (start + timedelta(days=2, hours=15)).isoformat(),
            "state": "APPROVED"
        })

        return {"commits": commits, "pulls": pulls, "reviews": reviews}
