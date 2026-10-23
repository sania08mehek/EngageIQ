"""
EngageIQ Data Integration Pipeline - Step 4: Timezone Normalization & Noise Reduction
Converts all timestamps to UTC, projects to Employee local timezone for working-hour analysis,
and filters automated bot/broadcast noise.
"""

from datetime import datetime, timezone, time
from typing import Optional, Any, Dict
from zoneinfo import ZoneInfo
import re


class TimeZoneHelper:
    """Handles UTC conversions and employee local working hours detection."""

    @staticmethod
    def parse_to_utc(raw_ts: Any) -> Optional[datetime]:
        """Parses various platform timestamp formats into a UTC datetime."""
        if raw_ts is None:
            return None
            
        if isinstance(raw_ts, datetime):
            if raw_ts.tzinfo is None:
                return raw_ts.replace(tzinfo=timezone.utc)
            return raw_ts.astimezone(timezone.utc)

        # Unix float timestamp (Slack: "1729340000.123456")
        if isinstance(raw_ts, (int, float)):
            return datetime.fromtimestamp(float(raw_ts), tz=timezone.utc)

        ts_str = str(raw_ts).strip()
        
        # Slack numeric string
        if re.match(r"^\d+(\.\d+)?$", ts_str):
            try:
                return datetime.fromtimestamp(float(ts_str), tz=timezone.utc)
            except (ValueError, OverflowError):
                pass

        # ISO 8601 variations (GitHub, Jira, Calendar)
        # Normalize Jira "+0000" to "+00:00"
        ts_str = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", ts_str)
        
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        except ValueError:
            # Fallback for date-only formats YYYY-MM-DD
            try:
                dt = datetime.strptime(ts_str[:10], "%Y-%m-%d")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                return None

    @staticmethod
    def is_after_hours(
        utc_dt: datetime,
        tz_name: str = "UTC",
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        work_days: Optional[list] = None
    ) -> bool:
        """
        Determines if a UTC event occurred outside the employee's local working hours or on weekends.
        Work days default: Mon(0) - Fri(4).
        """
        if utc_dt is None:
            return False

        if work_days is None:
            work_days = [0, 1, 2, 3, 4]  # Monday through Friday

        try:
            local_tz = ZoneInfo(tz_name)
            local_dt = utc_dt.astimezone(local_tz)
        except Exception:
            local_dt = utc_dt  # fallback to UTC if timezone name invalid

        # 1. Weekend check
        if local_dt.weekday() not in work_days:
            return True

        # 2. Daily working hours check (e.g. 9:00 AM - 6:00 PM)
        hour = local_dt.hour + (local_dt.minute / 60.0)
        if hour < work_start_hour or hour >= work_end_hour:
            return True

        return False


class NoiseFilter:
    """Filters platform-specific automated noise, broadcast channels, and invalid events."""

    IGNORED_SLACK_CHANNELS = {"general", "announcements", "all-hands", "random", "watercooler"}
    BOT_AUTHORS = {"dependabot", "dependabot[bot]", "github-actions[bot]", "renovate", "bot", "jira-bot"}

    @classmethod
    def is_valid_slack_message(cls, event: Dict[str, Any]) -> bool:
        """Excludes bot messages, automated subtypes, and public announcement channels."""
        # Bot exclusion
        if event.get("bot_id") or event.get("subtype") in ("bot_message", "channel_join", "channel_leave"):
            return False
            
        # Broadcast channel exclusion
        channel_name = str(event.get("channel_name", "")).lower().replace("#", "")
        if channel_name in cls.IGNORED_SLACK_CHANNELS:
            return False

        return True

    @classmethod
    def is_valid_github_event(cls, event: Dict[str, Any]) -> bool:
        """Excludes automated bot commits and PRs."""
        author = str(event.get("author") or event.get("user") or "").lower().strip()
        for bot in cls.BOT_AUTHORS:
            if bot in author:
                return False
                
        # Exclude automated message headers
        msg = str(event.get("commit_message", "")).lower()
        if "auto-generated" in msg or "bump version" in msg:
            return False
            
        return True

    @classmethod
    def is_valid_calendar_event(cls, event: Dict[str, Any], employee_email: str) -> bool:
        """Excludes declined meetings and all-day events."""
        # 1. All-day events (have 'date' instead of 'dateTime')
        start = event.get("start", {})
        if "date" in start and "dateTime" not in start:
            return False

        # 2. Declined meetings
        attendees = event.get("attendees", [])
        for att in attendees:
            if att.get("email", "").lower() == employee_email.lower():
                if att.get("responseStatus") == "declined":
                    return False

        return True
