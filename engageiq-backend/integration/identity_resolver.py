"""
EngageIQ Data Integration Pipeline - Step 1: Employee Identity & Mapping Layer
Unifies fragmented identities across GitHub, Slack, Jira, and Google Calendar into a single employee_id.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
import json
from pathlib import Path


@dataclass
class EmployeeIdentity:
    employee_id: str
    employee_name: str
    role: str
    team_id: str
    team_name: str
    email: str
    slack_user_id: Optional[str] = None
    jira_account_id: Optional[str] = None
    github_username: Optional[str] = None
    timezone: str = "UTC"
    work_start_hour: int = 9   # 9:00 AM
    work_end_hour: int = 18    # 6:00 PM (18:00)
    work_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri


class IdentityResolver:
    """
    Unified Identity Resolution Table.
    Maps platform-specific IDs (Slack U..., Jira UUID, GitHub username, work email)
    to a canonical employee_id and organizational team_id.
    """

    def __init__(self):
        self._by_employee_id: Dict[str, EmployeeIdentity] = {}
        self._by_email: Dict[str, EmployeeIdentity] = {}
        self._by_slack: Dict[str, EmployeeIdentity] = {}
        self._by_jira: Dict[str, EmployeeIdentity] = {}
        self._by_github: Dict[str, EmployeeIdentity] = {}

        # Initialize with standard employee seed directory
        self._seed_default_identities()

    def register_identity(self, identity: EmployeeIdentity):
        """Registers or updates an employee identity in the resolution index."""
        self._by_employee_id[identity.employee_id] = identity
        
        if identity.email:
            self._by_email[identity.email.lower().strip()] = identity
        if identity.slack_user_id:
            self._by_slack[identity.slack_user_id.strip()] = identity
        if identity.jira_account_id:
            self._by_jira[identity.jira_account_id.strip()] = identity
        if identity.github_username:
            self._by_github[identity.github_username.lower().strip()] = identity

    def resolve(self, platform: str, identifier: str) -> Optional[EmployeeIdentity]:
        """
        Resolves an external platform identifier to an EmployeeIdentity.
        
        Args:
            platform: 'slack', 'github', 'jira', 'email', or 'calendar'
            identifier: the external username/id/email
        """
        if not identifier:
            return None
            
        clean_id = str(identifier).strip()
        platform_key = platform.lower().strip()

        if platform_key in ("email", "calendar", "google_calendar"):
            return self._by_email.get(clean_id.lower())
        elif platform_key == "slack":
            return self._by_slack.get(clean_id) or self._by_email.get(clean_id.lower())
        elif platform_key == "jira":
            return self._by_jira.get(clean_id) or self._by_email.get(clean_id.lower())
        elif platform_key == "github":
            return self._by_github.get(clean_id.lower())
        elif platform_key == "employee_id":
            return self._by_employee_id.get(clean_id)
        
        return None

    def get_all_identities(self) -> List[EmployeeIdentity]:
        """Returns all registered employee identities."""
        return list(self._by_employee_id.values())

    def get_by_employee_id(self, employee_id: str) -> Optional[EmployeeIdentity]:
        return self._by_employee_id.get(employee_id)

    def _seed_default_identities(self):
        """Seeds realistic cross-platform test identities."""
        seeds = [
            EmployeeIdentity(
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
                work_end_hour=18,
            ),
            EmployeeIdentity(
                employee_id="EMP-9043",
                employee_name="Alex Rivera",
                role="Full Stack Engineer",
                team_id="TEAM-ENG-03",
                team_name="Core Platform",
                email="alex.rivera@company.com",
                slack_user_id="U02837465",
                jira_account_id="6c21bd9e93f16c33dd8e5fa6",
                github_username="arivera-code",
                timezone="America/Chicago",
                work_start_hour=9,
                work_end_hour=18,
            ),
            EmployeeIdentity(
                employee_id="EMP-9044",
                employee_name="Elena Rostova",
                role="Lead Product Designer",
                team_id="TEAM-DES-01",
                team_name="Product Design",
                email="elena.rostova@company.com",
                slack_user_id="U03746582",
                jira_account_id="7d32ce0f04a27d44ee9f6ab7",
                github_username=None,  # Designers don't typically commit code (tested in graceful degradation)
                timezone="Europe/London",
                work_start_hour=9,
                work_end_hour=17,
            ),
            EmployeeIdentity(
                employee_id="EMP-9045",
                employee_name="Marcus Vance",
                role="Engineering Manager",
                team_id="TEAM-ENG-03",
                team_name="Core Platform",
                email="marcus.vance@company.com",
                slack_user_id="U04857693",
                jira_account_id="8e43df1a15b38e55ff0a7bc8",
                github_username="mvance-lead",
                timezone="America/New_York",
                work_start_hour=8,
                work_end_hour=18,
            ),
            EmployeeIdentity(
                employee_id="EMP-9046",
                employee_name="Jordan Patel",
                role="Account Executive",
                team_id="TEAM-SLS-02",
                team_name="Enterprise Sales",
                email="jordan.patel@company.com",
                slack_user_id="U05968704",
                jira_account_id="9f54ea2b26c49f66aa1b8cd9",
                github_username=None,
                timezone="America/Los_Angeles",
                work_start_hour=8,
                work_end_hour=17,
            )
        ]
        for s in seeds:
            self.register_identity(s)


identity_resolver = IdentityResolver()
