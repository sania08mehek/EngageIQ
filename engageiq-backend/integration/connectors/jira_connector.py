"""
Jira Connector
Extracts and parses Jira issues and changelogs:
- completion_rate: Completed issues / Total assigned issues within sprint or time window
- velocity: Total story points completed (customfield_10002)
- deadline_adherence: Tasks completed on or before duedate / Total completed tasks with duedates
- rework_ratio (Jira part): Reopened tickets (moved back from Done to In Progress) / Total completed items
- Activity events for after_hours_ratio calculation
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from integration.noise_filter import TimeZoneHelper


class JiraConnector:
    """Parses Jira issues, status changes, and changelog revisions."""

    COMPLETED_STATUSES = {"done", "closed", "resolved", "complete", "finished"}

    @staticmethod
    def process_jira_issues(
        issues: List[Dict[str, Any]],
        jira_account_id: str,
        period_start_utc: datetime,
        period_end_utc: datetime
    ) -> Dict[str, Any]:
        """
        Processes assigned Jira issues and changelogs for an employee.
        
        Returns:
            {
                "completion_rate": float,       # [0, 1]
                "velocity": float,              # total story points
                "deadline_adherence": float,    # [0, 1]
                "reopened_tickets_count": int,
                "total_completed_count": int,
                "activity_timestamps": List[datetime]
            }
        """
        assigned_count = 0
        completed_count = 0
        total_story_points = 0.0

        due_date_total = 0
        on_time_total = 0
        reopened_count = 0
        activity_timestamps: List[datetime] = []

        for issue in issues:
            fields = issue.get("fields", issue)
            
            # Check assignee match
            assignee = fields.get("assignee") or {}
            assignee_id = assignee.get("accountId") or assignee.get("name") or assignee.get("id")
            if str(assignee_id) != str(jira_account_id):
                continue

            assigned_count += 1

            # Log updated timestamp for after-hours
            updated_ts = TimeZoneHelper.parse_to_utc(fields.get("updated"))
            if updated_ts and period_start_utc <= updated_ts <= period_end_utc:
                activity_timestamps.append(updated_ts)

            # Check completion
            status = str(fields.get("status", {}).get("name", "")).lower()
            resolution_date_raw = fields.get("resolutiondate") or fields.get("resolved")
            resolution_dt = TimeZoneHelper.parse_to_utc(resolution_date_raw)

            is_completed = (status in JiraConnector.COMPLETED_STATUSES) or (resolution_dt is not None)

            if is_completed:
                # Check if resolved within period window
                if resolution_dt and period_start_utc <= resolution_dt <= period_end_utc:
                    completed_count += 1
                    
                    # Velocity: extract story points from customfield_10002 or story_points field
                    sp = (
                        fields.get("customfield_10002") or
                        fields.get("customfield_10016") or
                        fields.get("story_points") or
                        fields.get("points") or
                        0.0
                    )
                    try:
                        total_story_points += float(sp)
                    except (ValueError, TypeError):
                        pass

                    # Deadline adherence
                    duedate_raw = fields.get("duedate")
                    if duedate_raw:
                        due_dt = TimeZoneHelper.parse_to_utc(duedate_raw)
                        if due_dt:
                            due_date_total += 1
                            # On-time if resolution date is before or on the due date (end of that due date)
                            if resolution_dt <= due_dt:
                                on_time_total += 1

            # Changelog inspection for reopen rework
            changelog = issue.get("changelog", {})
            histories = changelog.get("histories", [])
            for h in histories:
                h_dt = TimeZoneHelper.parse_to_utc(h.get("created"))
                if h_dt and period_start_utc <= h_dt <= period_end_utc:
                    for item in h.get("items", []):
                        if item.get("field") == "status":
                            from_str = str(item.get("fromString", "")).lower()
                            to_str = str(item.get("toString", "")).lower()
                            # Reopened: moved from done/resolved back to in progress or open
                            if from_str in JiraConnector.COMPLETED_STATUSES and to_str not in JiraConnector.COMPLETED_STATUSES:
                                reopened_count += 1

        # Calculate metrics
        completion_rate = round(completed_count / assigned_count, 4) if assigned_count > 0 else 0.85
        deadline_adherence = round(on_time_total / due_date_total, 4) if due_date_total > 0 else 0.90

        return {
            "completion_rate": completion_rate,
            "velocity": round(total_story_points, 1),
            "deadline_adherence": deadline_adherence,
            "reopened_tickets_count": reopened_count,
            "total_completed_count": completed_count,
            "assigned_count": assigned_count,
            "activity_timestamps": activity_timestamps
        }
