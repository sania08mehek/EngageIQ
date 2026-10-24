"""
Slack Connector
Extracts and parses Slack conversations:
- response_latency: Average duration between receiving direct mention/DM and posting a reply (in minutes)
- Activity events for after_hours_ratio calculation
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from integration.noise_filter import TimeZoneHelper, NoiseFilter


class SlackConnector:
    """Computes response latency from direct mentions and DMs and extracts activity timestamps."""

    @staticmethod
    def process_slack_events(
        messages: List[Dict[str, Any]],
        slack_user_id: str,
        period_start_utc: datetime,
        period_end_utc: datetime
    ) -> Dict[str, Any]:
        """
        Processes Slack conversation messages:
        - Matches mentions (<@U12345678>) or DMs to employee replies
        - Computes latency in minutes
        - Collects all authored event timestamps
        
        Returns:
            {
                "response_latency_minutes": float,
                "response_count": int,
                "activity_timestamps": List[datetime]
            }
        """
        mention_tag = f"<@{slack_user_id}>"
        authored_timestamps: List[datetime] = []
        latencies_minutes: List[float] = []

        # Sort messages chronologically by timestamp
        parsed_msgs = []
        for msg in messages:
            if not NoiseFilter.is_valid_slack_message(msg):
                continue

            ts = TimeZoneHelper.parse_to_utc(msg.get("ts"))
            if ts and period_start_utc <= ts <= period_end_utc:
                parsed_msgs.append({
                    "ts": ts,
                    "user": msg.get("user"),
                    "text": str(msg.get("text", "")),
                    "thread_ts": msg.get("thread_ts"),
                    "channel_type": msg.get("channel_type", "channel"), # 'im', 'mpim', 'channel'
                    "channel_id": msg.get("channel", "C01")
                })
                
                # If authored by the target employee, record for after-hours calculations
                if msg.get("user") == slack_user_id:
                    authored_timestamps.append(ts)

        parsed_msgs.sort(key=lambda x: x["ts"])

        # Match incoming mentions / DMs with replies
        # Window: messages where someone else mentions employee, followed by employee's reply in thread or channel
        for i, incoming in enumerate(parsed_msgs):
            is_incoming = incoming["user"] != slack_user_id
            is_mention = mention_tag in incoming["text"]
            is_dm = incoming["channel_type"] in ("im", "mpim")

            if is_incoming and (is_mention or is_dm):
                # Search forward for employee's reply
                for reply in parsed_msgs[i + 1:]:
                    if reply["user"] == slack_user_id:
                        # Match thread or DM channel
                        same_thread = incoming.get("thread_ts") and incoming["thread_ts"] == reply.get("thread_ts")
                        same_dm = is_dm and incoming["channel_id"] == reply["channel_id"]
                        
                        if same_thread or same_dm:
                            diff_minutes = (reply["ts"] - incoming["ts"]).total_seconds() / 60.0
                            # Discard unrealistic latencies (e.g. > 48 hours)
                            if 0.5 <= diff_minutes <= 2880.0:
                                latencies_minutes.append(diff_minutes)
                            break

        avg_latency = round(sum(latencies_minutes) / len(latencies_minutes), 2) if latencies_minutes else 15.0

        return {
            "response_latency_minutes": avg_latency,
            "response_count": len(latencies_minutes),
            "activity_timestamps": authored_timestamps
        }
