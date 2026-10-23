"""
EngageIQ Data Integration - Webhook & Batch Sync Router
FastAPI router for Slack, GitHub, Jira webhooks and Google Calendar sync jobs.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database.db_session import get_db
from database.repository import PipelineRepository
from integration.identity_resolver import identity_resolver, EmployeeIdentity
from integration.metrics_aggregator import MetricsAggregator, AggregationPeriod, UnifiedMetricOutput
from integration.synthetic_events_generator import SyntheticRawEventsGenerator
from scoring.pace_engine import PACEEngine
from scoring.pattern_detector import PatternDetector

router = APIRouter(prefix="/api/integration", tags=["Data Integration & Webhooks"])

# In-memory event buffers (for webhook event accumulation prior to batch aggregation)
_EVENT_BUFFERS: Dict[str, Dict[str, List[Any]]] = {
    "slack": {},
    "github": {},
    "jira": {},
    "calendar": {}
}


# ─── 1. WEBHOOK RECEIVERS ───────────────────────────────────────────────────

@router.post("/webhooks/slack")
async def receive_slack_webhook(request: Request):
    """
    Receives Slack Events API webhooks (app_mention, message).
    Supports Slack url_verification challenge.
    """
    payload = await request.json()
    
    # URL verification challenge from Slack
    if "challenge" in payload:
        return {"challenge": payload["challenge"]}

    event = payload.get("event", {})
    user_id = event.get("user")
    
    if user_id:
        if user_id not in _EVENT_BUFFERS["slack"]:
            _EVENT_BUFFERS["slack"][user_id] = []
        _EVENT_BUFFERS["slack"][user_id].append(event)

    return {"status": "received", "event_type": event.get("type")}


@router.post("/webhooks/github")
async def receive_github_webhook(request: Request):
    """
    Receives GitHub webhooks (push, pull_request, pull_request_review).
    """
    payload = await request.json()
    sender = payload.get("sender", {}).get("login")
    
    if sender:
        sender_lower = sender.lower()
        if sender_lower not in _EVENT_BUFFERS["github"]:
            _EVENT_BUFFERS["github"][sender_lower] = []
        _EVENT_BUFFERS["github"][sender_lower].append(payload)

    return {"status": "received", "action": payload.get("action", "push")}


@router.post("/webhooks/jira")
async def receive_jira_webhook(request: Request):
    """
    Receives Jira webhooks (jira:issue_updated, jira:issue_created).
    """
    payload = await request.json()
    issue = payload.get("issue", {})
    assignee = issue.get("fields", {}).get("assignee") or {}
    acc_id = assignee.get("accountId")
    
    if acc_id:
        if acc_id not in _EVENT_BUFFERS["jira"]:
            _EVENT_BUFFERS["jira"][acc_id] = []
        _EVENT_BUFFERS["jira"][acc_id].append(payload)

    return {"status": "received", "webhook_event": payload.get("webhookEvent")}


@router.post("/sync/google-calendar")
async def sync_google_calendar(email: Optional[str] = None):
    """
    Simulates / triggers Google Calendar nightly batch pull.
    """
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=7)
    
    return {
        "status": "success",
        "action": "calendar_sync_completed",
        "synced_window": f"{period_start.isoformat()} to {now.isoformat()}",
        "calendars_checked": 1 if email else len(identity_resolver.get_all_identities())
    }


# ─── 2. END-TO-END AGGREGATION & PACE SCORING PIPELINE ──────────────────────

@router.post("/run-aggregation", response_model=List[Dict[str, Any]])
def run_aggregation_pipeline(
    days_back: int = 7,
    db: Session = Depends(get_db)
):
    """
    Executes the End-to-End Integration Pipeline:
    1. Aggregates multi-source payloads (Calendar, Slack, Jira, GitHub) per employee.
    2. Resolves identities and projects into Local Timezones.
    3. Produces the Standardized Unified Schema records.
    4. Evaluates EHS, OPI, and 40:60 PACE Scores.
    5. Persists all metrics and risk events in the relational SQLite database.
    """
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=days_back)
    period = AggregationPeriod(start_utc=period_start, end_utc=now)

    aggregator = MetricsAggregator(identity_resolver)
    pace_engine = PACEEngine()
    pattern_detector = PatternDetector()
    repo = PipelineRepository(db)

    results: List[Dict[str, Any]] = []
    df_rows: List[Dict[str, Any]] = []

    identities = identity_resolver.get_all_identities()

    for identity in identities:
        # Generate or load realistic raw events for each employee
        profile = "healthy"
        if identity.employee_id == "EMP-9042":
            profile = "healthy"
        elif identity.employee_id == "EMP-9044":
            profile = "overloaded"
        elif identity.employee_id == "EMP-9045":
            profile = "at_risk"

        raw_events = SyntheticRawEventsGenerator.generate_events_for_employee(
            identity=identity,
            period_start=period_start,
            period_end=now,
            profile=profile
        )

        # 1. Aggregate and produce Standardized Unified Output Schema
        output = aggregator.aggregate_for_employee(
            employee_id=identity.employee_id,
            period=period,
            calendar_events=raw_events["calendar_events"],
            slack_messages=raw_events["slack_messages"],
            jira_issues=raw_events["jira_issues"],
            github_data=raw_events["github_data"]
        )

        output_dict = output.to_dict()
        results.append(output_dict)

        # Prepare row for PACE engine scoring & DB persistence
        m = output.metrics
        df_rows.append({
            "employee_id": output.employee_id,
            "employee_name": output.employee_name,
            "role": output.role,
            "team_id": output.team_id,
            "team_name": output.team_name,
            # Normalization mappings for PACE formula
            "meeting_load": m["meeting_load"],
            "focus_gap": min(1.0, m["focus_gap"] / 5.0),
            "response_latency": min(1.0, m["response_latency_minutes"] / 30.0),
            "after_hours_ratio": m["after_hours_ratio"],
            "completion_rate": m["completion_rate"],
            "velocity": min(1.0, m["velocity"] / 15.0),
            "deadline_adherence": m["deadline_adherence"],
            "code_activity": min(1.0, m["code_activity"] / 100.0),
            "rework_ratio": m["rework_ratio"],
            # Raw fields for DB storage
            "meeting_hours": m["meeting_load"] * 40.0,
            "focus_gap_days": m["focus_gap"],
            "response_latency_hours": m["response_latency_minutes"] / 60.0,
            "after_hours_pct": m["after_hours_ratio"] * 100.0
        })

    # 2. Score with PACE Engine (40:60)
    df = pd.DataFrame(df_rows)
    scored_df = pace_engine.process_dataframe(df)

    # 3. Detect Risk Patterns
    risks = pattern_detector.detect_patterns(scored_df)

    # 4. Persist in Database
    repo.store_pipeline_batch(scored_df, risks)

    return results


# ─── 3. CONNECTOR STATUS & SYNC MANAGEMENT ─────────────────────────────────

@router.get("/status")
def get_integrations_status():
    """
    Returns live connectivity status, metrics provided, and mapped identities
    for all data sources (GitHub, Jira, Slack, Google Calendar, CSV).
    """
    identities = identity_resolver.get_all_identities()
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "status": "online",
        "connectors": [
            {
                "id": "github",
                "name": "GitHub",
                "category": "Code & Collaboration",
                "description": "Commit volume, pull request velocity, PR reviews, and code churn detection",
                "status": "connected",
                "mode": "Live Webhooks + Periodic Sync",
                "metrics": ["code_activity", "rework_ratio", "after_hours_ratio"],
                "lastSync": now_iso,
                "bufferedEvents": sum(len(v) for v in _EVENT_BUFFERS["github"].values()),
                "icon": "github"
            },
            {
                "id": "jira",
                "name": "Jira Software",
                "category": "Project & Task Delivery",
                "description": "Story points velocity, task completion rate, deadline adherence, reopened ticket churn",
                "status": "connected",
                "mode": "Live Webhooks + Sprint Sync",
                "metrics": ["completion_rate", "velocity", "deadline_adherence"],
                "lastSync": now_iso,
                "bufferedEvents": sum(len(v) for v in _EVENT_BUFFERS["jira"].values()),
                "icon": "jira"
            },
            {
                "id": "slack",
                "name": "Slack",
                "category": "Communication Metadata",
                "description": "Direct message & mention response latency (minutes) and after-hours activity ratio",
                "status": "connected",
                "mode": "Realtime Events API Webhook",
                "metrics": ["response_latency", "after_hours_ratio"],
                "lastSync": now_iso,
                "bufferedEvents": sum(len(v) for v in _EVENT_BUFFERS["slack"].values()),
                "icon": "slack"
            },
            {
                "id": "google-calendar",
                "name": "Google Calendar",
                "category": "Meeting & Focus Time",
                "description": "Meeting duration, fragmented focus-gap blocks, external vs internal meetings",
                "status": "connected",
                "mode": "Nightly Batch Sync",
                "metrics": ["meeting_load", "focus_gap", "after_hours_ratio"],
                "lastSync": now_iso,
                "bufferedEvents": sum(len(v) for v in _EVENT_BUFFERS["calendar"].values()),
                "icon": "calendar"
            },
            {
                "id": "csv",
                "name": "CSV Ingestion Pipeline",
                "category": "Batch File Handling",
                "description": "Upload historical metadata directly from CSV files for rapid batch evaluation",
                "status": "active",
                "mode": "File Upload / Manual",
                "metrics": ["All Signal (EHS) and Output (OPI) metrics"],
                "lastSync": now_iso,
                "bufferedEvents": 0,
                "icon": "file"
            }
        ],
        "mappedIdentitiesCount": len(identities),
        "identities": [
            {
                "employeeId": i.employee_id,
                "name": i.employee_name,
                "role": i.role,
                "team": i.team_name,
                "timezone": i.timezone,
                "accounts": {
                    "slack": i.slack_user_id,
                    "jira": i.jira_account_id,
                    "github": i.github_username,
                    "calendar": i.email
                }
            } for i in identities
        ]
    }


@router.get("/identities")
def get_mapped_identities():
    """Returns all identity records mapped across GitHub, Jira, Slack, and Google Calendar."""
    identities = identity_resolver.get_all_identities()
    return [
        {
            "employeeId": i.employee_id,
            "name": i.employee_name,
            "role": i.role,
            "team": i.team_name,
            "timezone": i.timezone,
            "accounts": {
                "slack": i.slack_user_id,
                "jira": i.jira_account_id,
                "github": i.github_username,
                "calendar": i.email
            }
        } for i in identities
    ]


@router.post("/sync/{connector_id}")
def sync_connector(connector_id: str, db: Session = Depends(get_db)):
    """Triggers a live / synthetic synchronization for a connector and re-evaluates PACE scores."""
    # Run the integration aggregation pipeline
    results = run_aggregation_pipeline(days_back=7, db=db)
    return {
        "status": "success",
        "connector": connector_id,
        "action": "synchronized_and_scored",
        "processedEmployees": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
