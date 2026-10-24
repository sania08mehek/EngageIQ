"""
EngageIQ Data Integration Pipeline - CLI Runner
Runs multi-source API aggregation (Calendar, Slack, Jira, GitHub) -> Unified Metrics -> PACE Scoring.

Usage:
    python run_integration.py
    python run_integration.py --employee EMP-9042
"""

import argparse
import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd

PIPELINE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PIPELINE_ROOT))

from integration.identity_resolver import identity_resolver
from integration.metrics_aggregator import MetricsAggregator, AggregationPeriod
from integration.synthetic_events_generator import SyntheticRawEventsGenerator
from scoring.pace_engine import PACEEngine
from scoring.pattern_detector import PatternDetector
from database.db_session import SessionLocal, init_db
from database.repository import PipelineRepository


def run_integration_pipeline(target_employee_id: str = None):
    print("\n" + "=" * 78)
    print("      ENGAGEIQ MULTI-SOURCE DATA INTEGRATION & PACE PIPELINE")
    print("   Google Calendar + Slack + Jira + GitHub -> Standardized Schema -> PACE")
    print("=" * 78)

    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=7)
    period = AggregationPeriod(start_utc=period_start, end_utc=now)

    print(f"\n[+] Step 1: Processing Aggregation Window")
    print(f"    Period: {period.start_utc.isoformat()} to {period.end_utc.isoformat()}")

    aggregator = MetricsAggregator(identity_resolver)
    pace_engine = PACEEngine()
    pattern_detector = PatternDetector()

    all_identities = identity_resolver.get_all_identities()
    if target_employee_id:
        all_identities = [i for i in all_identities if i.employee_id == target_employee_id]
        if not all_identities:
            print(f"[-] Error: Employee {target_employee_id} not found in Identity Resolver.")
            return

    print(f"\n[+] Step 2: Ingesting & Resolving Identities ({len(all_identities)} employees)")

    unified_records = []
    df_rows = []

    for identity in all_identities:
        print(f"\n--- Resolving: {identity.employee_name} ({identity.employee_id}) ---")
        print(f"    Role: {identity.role} | Team: {identity.team_name} | TZ: {identity.timezone}")
        print(f"    Accounts: Slack={identity.slack_user_id}, Jira={identity.jira_account_id}, GitHub={identity.github_username}")

        # Profile simulation
        profile = "healthy" if identity.employee_id == "EMP-9042" else "overloaded" if identity.employee_id == "EMP-9044" else "healthy"
        raw_events = SyntheticRawEventsGenerator.generate_events_for_employee(
            identity=identity,
            period_start=period_start,
            period_end=now,
            profile=profile
        )

        # Multi-source aggregation
        unified_output = aggregator.aggregate_for_employee(
            employee_id=identity.employee_id,
            period=period,
            calendar_events=raw_events["calendar_events"],
            slack_messages=raw_events["slack_messages"],
            jira_issues=raw_events["jira_issues"],
            github_data=raw_events["github_data"]
        )

        output_dict = unified_output.to_dict()
        unified_records.append(output_dict)

        print(f"    [OK] Standardized Unified Output Generated:")
        print(json.dumps(output_dict, indent=4))

        # Row for PACE scoring
        m = unified_output.metrics
        df_rows.append({
            "employee_id": unified_output.employee_id,
            "employee_name": unified_output.employee_name,
            "role": unified_output.role,
            "team_id": unified_output.team_id,
            "team_name": unified_output.team_name,
            "meeting_load": m["meeting_load"],
            "focus_gap": min(1.0, m["focus_gap"] / 5.0),
            "response_latency": min(1.0, m["response_latency_minutes"] / 30.0),
            "after_hours_ratio": m["after_hours_ratio"],
            "completion_rate": m["completion_rate"],
            "velocity": min(1.0, m["velocity"] / 15.0),
            "deadline_adherence": m["deadline_adherence"],
            "code_activity": min(1.0, m["code_activity"] / 100.0),
            "rework_ratio": m["rework_ratio"],
            "meeting_hours": m["meeting_load"] * 40.0,
            "focus_gap_days": m["focus_gap"],
            "response_latency_hours": m["response_latency_minutes"] / 60.0,
            "after_hours_pct": m["after_hours_ratio"] * 100.0
        })

    # Step 3: Scoring & Database Persistence
    print(f"\n[+] Step 3: Fusing into 40:60 PACE Scores & Relational Persistence")
    df = pd.DataFrame(df_rows)
    scored_df = pace_engine.process_dataframe(df)
    risks = pattern_detector.detect_patterns(scored_df)

    init_db()
    db = SessionLocal()
    try:
        repo = PipelineRepository(db)
        stored_count = repo.store_pipeline_batch(scored_df, risks)
        print(f"    [OK] Persisted {stored_count} records and {len(risks)} risk events into SQLite database.")
    finally:
        db.close()

    print("\n" + "=" * 78)
    print(f"{'EMP ID':<10} {'NAME':<18} {'ROLE':<22} {'EHS':<6} {'OPI':<6} {'PACE':<6} {'RISK':<10}")
    print("-" * 78)
    for _, row in scored_df.iterrows():
        print(
            f"{row['employee_id']:<10} "
            f"{str(row['employee_name'])[:16]:<18} "
            f"{str(row['role'])[:20]:<22} "
            f"{row['ehs_score']:<6.2f} "
            f"{row['opi_score']:<6.2f} "
            f"{row['pace_score']:<6.2f} "
            f"{row['risk_category']:<10}"
        )
    print("=" * 78)
    print("\n[OK] Integration Pipeline Finished Successfully!\n")


def main():
    parser = argparse.ArgumentParser(description="EngageIQ Multi-Source Data Integration Pipeline")
    parser.add_argument("--employee", type=str, default=None, help="Target employee_id (e.g. EMP-9042)")
    args = parser.parse_args()

    run_integration_pipeline(target_employee_id=args.employee)


if __name__ == "__main__":
    main()
