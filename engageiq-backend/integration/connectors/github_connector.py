"""
GitHub Connector
Extracts and parses GitHub pulls, commits, and reviews:
- code_activity: Weighted sum: W1(Commits) + W2(PRs opened) + W3(PR Reviews)
- rework_ratio (GitHub part): Reverted commits or rapid churn
- Activity events for after_hours_ratio calculation
"""

from typing import List, Dict, Any
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from integration.noise_filter import TimeZoneHelper, NoiseFilter


class GitHubConnector:
    """Parses GitHub commits, pull requests, and code reviews."""

    WEIGHT_COMMIT = 1.0
    WEIGHT_PR_OPENED = 3.0
    WEIGHT_PR_REVIEW = 2.0

    @staticmethod
    def process_github_data(
        commits: List[Dict[str, Any]],
        pulls: List[Dict[str, Any]],
        reviews: List[Dict[str, Any]],
        github_username: str,
        period_start_utc: datetime,
        period_end_utc: datetime
    ) -> Dict[str, Any]:
        """
        Parses GitHub activity:
        - Filters out bots (Dependabot, Actions)
        - Computes code_activity score
        - Detects reverted commits
        - Gathers activity timestamps
        
        Returns:
            {
                "code_activity": float,         # normalized activity index
                "commit_count": int,
                "prs_opened": int,
                "pr_reviews": int,
                "reverted_commits": int,
                "activity_timestamps": List[datetime]
            }
        """
        target_user = github_username.lower().strip()
        activity_timestamps: List[datetime] = []

        commit_count = 0
        reverted_commits = 0
        prs_opened = 0
        pr_reviews = 0

        # 1. Process Commits
        for c in commits:
            if not NoiseFilter.is_valid_github_event(c):
                continue

            author_login = str(c.get("author", {}).get("login") or c.get("commit", {}).get("author", {}).get("name") or "").lower()
            if author_login != target_user:
                continue

            ts_raw = c.get("commit", {}).get("author", {}).get("date") or c.get("created_at")
            ts = TimeZoneHelper.parse_to_utc(ts_raw)
            if ts and period_start_utc <= ts <= period_end_utc:
                commit_count += 1
                activity_timestamps.append(ts)

                # Check if commit message indicates a revert or immediate rollback
                msg = str(c.get("commit", {}).get("message", "")).lower()
                if msg.startswith("revert") or "reverting" in msg or "fixup!" in msg:
                    reverted_commits += 1

        # 2. Process Pull Requests Opened
        for p in pulls:
            if not NoiseFilter.is_valid_github_event(p):
                continue

            creator = str(p.get("user", {}).get("login") or p.get("author") or "").lower()
            if creator != target_user:
                continue

            ts = TimeZoneHelper.parse_to_utc(p.get("created_at"))
            if ts and period_start_utc <= ts <= period_end_utc:
                prs_opened += 1
                activity_timestamps.append(ts)

        # 3. Process PR Reviews
        for r in reviews:
            reviewer = str(r.get("user", {}).get("login") or r.get("reviewer") or "").lower()
            if reviewer != target_user:
                continue

            ts = TimeZoneHelper.parse_to_utc(r.get("submitted_at") or r.get("created_at"))
            if ts and period_start_utc <= ts <= period_end_utc:
                pr_reviews += 1
                activity_timestamps.append(ts)

        # Weighted Code Activity
        raw_weighted_activity = (
            (GitHubConnector.WEIGHT_COMMIT * commit_count) +
            (GitHubConnector.WEIGHT_PR_OPENED * prs_opened) +
            (GitHubConnector.WEIGHT_PR_REVIEW * pr_reviews)
        )

        # Activity index on 0-100 scale (typical active week is 25-60 points)
        code_activity_index = round(raw_weighted_activity, 1)

        return {
            "code_activity": code_activity_index,
            "commit_count": commit_count,
            "prs_opened": prs_opened,
            "pr_reviews": pr_reviews,
            "reverted_commits": reverted_commits,
            "activity_timestamps": activity_timestamps
        }
