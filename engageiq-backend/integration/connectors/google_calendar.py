"""
Google Calendar Connector
Extracts and parses calendar events:
- meeting_load: Total accepted meeting hours over working hours (e.g. 40 hrs/wk)
- focus_gap: Average unbroken focus blocks between meetings during work hours (>= 2 consecutive hours)
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from integration.noise_filter import TimeZoneHelper, NoiseFilter


class GoogleCalendarConnector:
    """Extracts meeting hours and unbroken focus periods from Google Calendar events."""

    @staticmethod
    def process_calendar_events(
        events: List[Dict[str, Any]],
        employee_email: str,
        period_start_utc: datetime,
        period_end_utc: datetime,
        tz_name: str = "UTC",
        work_start_hour: int = 9,
        work_end_hour: int = 18,
        standard_work_hours: float = 40.0
    ) -> Dict[str, float]:
        """
        Parses Google Calendar events for a given employee and window.
        
        Returns:
            {
                "meeting_hours": float,
                "meeting_load": float, # ratio [0, 1]
                "focus_gap": float,    # average unbroken focus hours (>=2h)
                "focus_blocks_count": int
            }
        """
        accepted_intervals: List[Tuple[datetime, datetime]] = []
        total_meeting_seconds = 0.0

        for evt in events:
            if not NoiseFilter.is_valid_calendar_event(evt, employee_email):
                continue

            start_raw = evt.get("start", {}).get("dateTime")
            end_raw = evt.get("end", {}).get("dateTime")
            
            start_dt = TimeZoneHelper.parse_to_utc(start_raw)
            end_dt = TimeZoneHelper.parse_to_utc(end_raw)

            if not start_dt or not end_dt or start_dt >= end_dt:
                continue

            # Clip within the period window
            clipped_start = max(start_dt, period_start_utc)
            clipped_end = min(end_dt, period_end_utc)

            if clipped_start < clipped_end:
                duration = (clipped_end - clipped_start).total_seconds()
                total_meeting_seconds += duration
                accepted_intervals.append((clipped_start, clipped_end))

        # Sort and merge overlapping meeting intervals
        accepted_intervals.sort(key=lambda x: x[0])
        merged_intervals: List[Tuple[datetime, datetime]] = []
        for interval in accepted_intervals:
            if not merged_intervals:
                merged_intervals.append(interval)
            else:
                last_start, last_end = merged_intervals[-1]
                if interval[0] <= last_end:
                    merged_intervals[-1] = (last_start, max(last_end, interval[1]))
                else:
                    merged_intervals.append(interval)

        # 1. Compute meeting_load
        meeting_hours = total_meeting_seconds / 3600.0
        # If period is less than 7 days, scale standard hours accordingly
        days_in_period = max(1.0, (period_end_utc - period_start_utc).total_seconds() / 86400.0)
        expected_work_hours = min(standard_work_hours, days_in_period * (work_end_hour - work_start_hour))
        
        meeting_load = round(min(1.0, max(0.0, meeting_hours / expected_work_hours)), 4) if expected_work_hours > 0 else 0.0

        # 2. Compute focus_gap: unbroken blocks between meetings during working hours (>= 2 consecutive hours)
        focus_block_durations: List[float] = []
        
        # Iterate over each working day in the period
        try:
            local_tz = ZoneInfo(tz_name)
        except Exception:
            local_tz = ZoneInfo("UTC")

        curr_day = period_start_utc.astimezone(local_tz).date()
        end_day = period_end_utc.astimezone(local_tz).date()

        while curr_day <= end_day:
            if curr_day.weekday() in [0, 1, 2, 3, 4]:  # Monday-Friday
                day_start_local = datetime(curr_day.year, curr_day.month, curr_day.day, work_start_hour, 0, tzinfo=local_tz)
                day_end_local = datetime(curr_day.year, curr_day.month, curr_day.day, work_end_hour, 0, tzinfo=local_tz)
                
                day_start_utc = day_start_local.astimezone(ZoneInfo("UTC"))
                day_end_utc = day_end_local.astimezone(ZoneInfo("UTC"))

                # Find meetings on this day
                day_meetings = []
                for s, e in merged_intervals:
                    if s < day_end_utc and e > day_start_utc:
                        day_meetings.append((max(s, day_start_utc), min(e, day_end_utc)))

                # Scan free blocks
                pointer = day_start_utc
                for ms, me in day_meetings:
                    free_gap_hours = (ms - pointer).total_seconds() / 3600.0
                    if free_gap_hours >= 2.0:  # focus block threshold >= 2 hours
                        focus_block_durations.append(free_gap_hours)
                    pointer = max(pointer, me)

                # End of day block
                final_gap_hours = (day_end_utc - pointer).total_seconds() / 3600.0
                if final_gap_hours >= 2.0:
                    focus_block_durations.append(final_gap_hours)

            curr_day += timedelta(days=1)

        avg_focus_gap = round(sum(focus_block_durations) / len(focus_block_durations), 2) if focus_block_durations else 0.0

        return {
            "meeting_hours": round(meeting_hours, 2),
            "meeting_load": meeting_load,
            "focus_gap": avg_focus_gap,
            "focus_blocks_count": len(focus_block_durations)
        }
