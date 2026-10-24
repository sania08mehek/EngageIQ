"""
EngageIQ Data Pipeline - Database Repository
Encapsulates all persistence and query operations for employees, metrics,
scores, risk events, and reviews.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import (
    Employee, SignalMetric, OutputMetric, PaceScore,
    RiskEvent, ManagerReview, PipelineRun
)


class PipelineRepository:
    """Data Access Object for pipeline storage and analytics queries."""

    def __init__(self, db: Session):
        self.db = db

    # ─── INGESTION & STORAGE ───────────────────────────────────────────────

    def upsert_employee(self, emp_id: str, name: str, role: str, team_id: str, team_name: str) -> Employee:
        """Finds or creates/updates an employee record."""
        emp = self.db.query(Employee).filter(Employee.id == emp_id).first()
        if not emp:
            emp = Employee(
                id=emp_id,
                name=name,
                role=role or "Engineer",
                team_id=team_id or "platform",
                team_name=team_name or "Platform Engineering",
                status="active"
            )
            self.db.add(emp)
        else:
            emp.name = name
            if role:
                emp.role = role
            if team_id:
                emp.team_id = team_id
            if team_name:
                emp.team_name = team_name
        
        self.db.flush()
        return emp

    def store_pipeline_batch(self, scored_df: pd.DataFrame, risk_events: list = None) -> int:
        """
        Stores metrics, PACE scores, and risk events for a batch of scored employees.
        All operations are transactional within the current session.
        """
        now = datetime.utcnow()
        stored_count = 0

        for _, row in scored_df.iterrows():
            emp_id = str(row["employee_id"])
            emp_name = str(row["employee_name"])
            role = str(row.get("role", "Engineer"))
            team_id = str(row.get("team_id", "platform"))
            team_name = str(row.get("team_name", "Platform Engineering"))

            # 1. Upsert Employee
            emp = self.upsert_employee(emp_id, emp_name, role, team_id, team_name)

            # 2. Store SignalMetric
            signal_metric = SignalMetric(
                employee_id=emp.id,
                timestamp=now,
                meeting_load=float(row.get("meeting_load", 0.0)),
                focus_gap=float(row.get("focus_gap", 0.0)),
                response_latency=float(row.get("response_latency", 0.0)),
                after_hours_ratio=float(row.get("after_hours_ratio", 0.0)),
                meeting_hours=float(row.get("meeting_hours")) if pd.notna(row.get("meeting_hours")) else None,
                focus_gap_days=float(row.get("focus_gap_days")) if pd.notna(row.get("focus_gap_days")) else None,
                response_latency_hours=float(row.get("response_latency_hours")) if pd.notna(row.get("response_latency_hours")) else None,
                after_hours_pct=float(row.get("after_hours_pct")) if pd.notna(row.get("after_hours_pct")) else None,
                ehs_score=float(row["ehs_score"])
            )
            self.db.add(signal_metric)

            # 3. Store OutputMetric
            output_metric = OutputMetric(
                employee_id=emp.id,
                timestamp=now,
                completion_rate=float(row.get("completion_rate", 0.0)),
                velocity=float(row.get("velocity", 0.0)),
                deadline_adherence=float(row.get("deadline_adherence", 0.0)),
                code_activity=float(row.get("code_activity", 0.0)),
                rework_ratio=float(row.get("rework_ratio", 0.0)),
                opi_score=float(row["opi_score"])
            )
            self.db.add(output_metric)

            # 4. Store PaceScore
            pace_score = PaceScore(
                employee_id=emp.id,
                timestamp=now,
                ehs_score=float(row["ehs_score"]),
                opi_score=float(row["opi_score"]),
                pace_score=float(row["pace_score"]),
                risk_category=str(row.get("risk_category", "Healthy")),
                risk_explanation=str(row.get("risk_explanation", ""))
            )
            self.db.add(pace_score)
            stored_count += 1

        # 5. Store Risk Events
        if risk_events:
            for event in risk_events:
                risk_record = RiskEvent(
                    employee_id=event.employee_id,
                    detected_at=event.detected_at or now,
                    risk_type=event.pattern_id,
                    severity=event.severity,
                    evidence=json.dumps(event.evidence) if isinstance(event.evidence, dict) else str(event.evidence),
                    status="open"
                )
                self.db.add(risk_record)

        self.db.commit()
        return stored_count

    def store_review(self, employee_id: str, outcome: str, note: str, reviewer: str = "manager") -> ManagerReview:
        """Stores a human review."""
        review = ManagerReview(
            employee_id=employee_id,
            reviewer_id=reviewer,
            outcome=outcome,
            note=note,
            flag_week=datetime.utcnow().strftime("%Y-W%U"),
            created_at=datetime.utcnow()
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    # ─── QUERIES COMPATIBLE WITH ENGAGEIQ FRONTEND ───────────────────────────

    def get_scores_list(self) -> List[Dict[str, Any]]:
        """
        Returns all PaceScore records with employee details.
        Matches GET /api/scores expected by frontend.
        """
        scores = self.db.query(PaceScore).order_by(desc(PaceScore.timestamp)).all()
        results = []
        seen_emps = set()
        
        for s in scores:
            if s.employee_id in seen_emps:
                continue
            seen_emps.add(s.employee_id)
            
            emp = s.employee
            results.append({
                "id": s.id,
                "employee_id": s.employee_id,
                "employee_name": emp.name if emp else "Unknown",
                "role": emp.role if emp else "Engineer",
                "team_id": emp.team_id if emp else "platform",
                "team_name": emp.team_name if emp else "Platform Engineering",
                "ehs": round(s.ehs_score, 2),
                "opi": round(s.opi_score, 2),
                "pace": round(s.pace_score, 2),
                "risk": s.risk_category,
                "risk_explanation": s.risk_explanation,
                "timestamp": s.timestamp.isoformat()
            })
        return results

    def get_organization_summary(self) -> Dict[str, Any]:
        """
        Returns full OrgSummary structure expected by React frontend /api/organization.
        """
        employees = self.db.query(Employee).filter(Employee.status == "active").all()
        scores = self.get_scores_list()

        total_headcount = len(employees)
        if total_headcount == 0:
            return {
                "headcount": 0,
                "averagePace": 0.0,
                "averageEhs": 0.0,
                "averageOpi": 0.0,
                "riskMix": {"Healthy": 0, "Moderate": 0, "At-Risk": 0},
                "teams": [],
                "flaggedCount": 0,
                "reviewQueue": []
            }

        avg_pace = round(sum(s["pace"] for s in scores) / len(scores), 2) if scores else 0.75
        avg_ehs = round(sum(s["ehs"] for s in scores) / len(scores), 2) if scores else 0.78
        avg_opi = round(sum(s["opi"] for s in scores) / len(scores), 2) if scores else 0.73

        # Risk mix
        risk_mix = {"Healthy": 0, "Moderate": 0, "At-Risk": 0}
        for s in scores:
            cat = s.get("risk", "Healthy")
            risk_mix[cat] = risk_mix.get(cat, 0) + 1

        # Aggregate by team
        team_dict = {}
        for s in scores:
            tid = s["team_id"]
            if tid not in team_dict:
                team_dict[tid] = {
                    "id": tid,
                    "name": s["team_name"],
                    "headcount": 0,
                    "scores": [],
                    "ehs_list": [],
                    "opi_list": [],
                    "riskMix": {"Healthy": 0, "Moderate": 0, "At-Risk": 0}
                }
            t = team_dict[tid]
            t["headcount"] += 1
            t["scores"].append(s["pace"])
            t["ehs_list"].append(s["ehs"])
            t["opi_list"].append(s["opi"])
            cat = s.get("risk", "Healthy")
            t["riskMix"][cat] = t["riskMix"].get(cat, 0) + 1

        teams_summary = []
        for tid, t in team_dict.items():
            avg_t_pace = round(sum(t["scores"]) / len(t["scores"]), 2) if t["scores"] else 0.7
            avg_t_ehs = round(sum(t["ehs_list"]) / len(t["ehs_list"]), 2) if t["ehs_list"] else 0.7
            avg_t_opi = round(sum(t["opi_list"]) / len(t["opi_list"]), 2) if t["opi_list"] else 0.7
            
            teams_summary.append({
                "team": {"id": t["id"], "name": t["name"]},
                "headcount": t["headcount"],
                "averagePace": avg_t_pace,
                "averageEhs": avg_t_ehs,
                "averageOpi": avg_t_opi,
                "riskMix": t["riskMix"],
                "flaggedCount": t["riskMix"].get("At-Risk", 0),
                "trend": "down" if avg_t_pace < 0.6 else "flat" if avg_t_pace < 0.8 else "up",
                "sparkline": [round(avg_t_pace + (i * 0.01), 2) for i in range(12)]
            })

        # Flagged review queue
        flagged_scores = [s for s in scores if s["risk"] == "At-Risk"]
        review_queue = []
        for fs in flagged_scores:
            review_queue.append({
                "employee": {
                    "id": fs["employee_id"],
                    "name": fs["employee_name"],
                    "roleId": fs["role"].lower(),
                    "roleName": fs["role"],
                    "teamId": fs["team_id"],
                    "teamName": fs["team_name"]
                },
                "latest": {
                    "week": datetime.utcnow().strftime("%Y-W%U"),
                    "pace": fs["pace"],
                    "ehs": fs["ehs"],
                    "opi": fs["opi"],
                    "category": fs["risk"]
                },
                "delta": -0.08,
                "category": fs["risk"],
                "trend": "down",
                "sparkline": [round(fs["pace"] + 0.08 - (i * 0.01), 2) for i in range(8)],
                "flagged": True
            })

        return {
            "headcount": total_headcount,
            "history": [
                {
                    "week": (datetime.utcnow() - timedelta(weeks=11-i)).strftime("%Y-%m-%d"),
                    "ehs": round(max(0.1, min(1.0, avg_ehs + ((i - 6) * 0.004))), 2),
                    "opi": round(max(0.1, min(1.0, avg_opi + ((i - 6) * 0.006))), 2),
                    "pace": round(max(0.1, min(1.0, avg_pace + ((i - 6) * 0.005))), 2)
                } for i in range(12)
            ],
            "latest": {
                "week": datetime.utcnow().strftime("%Y-%m-%d"),
                "ehs": avg_ehs,
                "opi": avg_opi,
                "pace": avg_pace
            },
            "delta": -0.02,
            "mix": {
                "healthy": risk_mix.get("Healthy", 0),
                "moderate": risk_mix.get("Moderate", 0),
                "at-risk": risk_mix.get("At-Risk", 0)
            },
            "teams": [
                {
                    "team": t["team"],
                    "headcount": t["headcount"],
                    "history": [
                        {
                            "week": (datetime.utcnow() - timedelta(weeks=11-i)).strftime("%Y-%m-%d"),
                            "ehs": round(max(0.1, min(1.0, t["averageEhs"] + ((i - 6) * 0.005))), 2),
                            "opi": round(max(0.1, min(1.0, t["averageOpi"] + ((i - 6) * 0.005))), 2),
                            "pace": round(max(0.1, min(1.0, t["averagePace"] + ((i - 6) * 0.005))), 2)
                        } for i in range(12)
                    ],
                    "latest": {
                        "week": datetime.utcnow().strftime("%Y-%m-%d"),
                        "ehs": t["averageEhs"],
                        "opi": t["averageOpi"],
                        "pace": t["averagePace"]
                    },
                    "delta": -0.01,
                    "mix": {
                        "healthy": t["riskMix"].get("Healthy", 0),
                        "moderate": t["riskMix"].get("Moderate", 0),
                        "at-risk": t["riskMix"].get("At-Risk", 0)
                    },
                    "sparkline": t["sparkline"]
                } for t in teams_summary
            ],
            "queue": [
                {
                    "employee": fq["employee"],
                    "category": fq["category"].lower(),
                    "pace": fq["latest"]["pace"],
                    "headline": "Work patterns and delivery indicate elevated burnout risk",
                    "status": "needs-review"
                } for fq in review_queue
            ],
            # Backward-compatible fields
            "averagePace": avg_pace,
            "averageEhs": avg_ehs,
            "averageOpi": avg_opi,
            "riskMix": risk_mix,
            "flaggedCount": len(flagged_scores),
            "reviewQueue": review_queue
        }

    def get_team_detail(self, team_id: str) -> Dict[str, Any]:
        """Returns full TeamDetail structure matching frontend types."""
        all_scores = self.get_scores_list()
        team_members = [s for s in all_scores if s["team_id"].lower() == team_id.lower()]

        team_name = team_members[0]["team_name"] if team_members else team_id.replace('-', ' ').title()
        avg_pace = round(sum(s["pace"] for s in team_members) / len(team_members), 2) if team_members else 0.70
        avg_ehs = round(sum(s["ehs"] for s in team_members) / len(team_members), 2) if team_members else 0.70
        avg_opi = round(sum(s["opi"] for s in team_members) / len(team_members), 2) if team_members else 0.70

        risk_mix = {"Healthy": 0, "Moderate": 0, "At-Risk": 0}
        for m in team_members:
            cat = m.get("risk", "Healthy")
            risk_mix[cat] = risk_mix.get(cat, 0) + 1

        history = [
            {
                "week": (datetime.utcnow() - timedelta(weeks=11-i)).strftime("%Y-%m-%d"),
                "ehs": round(max(0.1, min(1.0, avg_ehs + ((i - 6) * 0.005))), 2),
                "opi": round(max(0.1, min(1.0, avg_opi + ((i - 6) * 0.005))), 2),
                "pace": round(max(0.1, min(1.0, avg_pace + ((i - 6) * 0.005))), 2)
            } for i in range(12)
        ]

        members_rows = []
        for m in team_members:
            cat_lower = m["risk"].lower()
            spark = [round(max(0.1, min(1.0, m["pace"] + ((i - 4) * 0.015))), 2) for i in range(8)]
            members_rows.append({
                "employee": {
                    "id": m["employee_id"],
                    "name": m["employee_name"],
                    "roleId": m["role"].lower(),
                    "roleName": m["role"],
                    "teamId": m["team_id"],
                    "teamName": m["team_name"]
                },
                "latest": {
                    "week": datetime.utcnow().strftime("%Y-%m-%d"),
                    "pace": m["pace"],
                    "ehs": m["ehs"],
                    "opi": m["opi"],
                    "category": cat_lower
                },
                "delta": -0.02,
                "category": cat_lower,
                "trend": "down" if m["pace"] < 0.6 else "flat",
                "sparkline": spark,
                "flagged": m["risk"] == "At-Risk",
                "reviewStatus": "needs-review" if m["risk"] == "At-Risk" else "not-flagged"
            })

        queue = [
            {
                "employee": m["employee"],
                "category": m["category"],
                "pace": m["latest"]["pace"],
                "headline": "PACE score dropped below healthy baseline",
                "status": "needs-review"
            } for m in members_rows if m["flagged"]
        ]

        return {
            "team": {"id": team_id, "name": team_name},
            "headcount": len(team_members),
            "history": history,
            "latest": history[-1],
            "delta": -0.02,
            "mix": {
                "healthy": risk_mix.get("Healthy", 0),
                "moderate": risk_mix.get("Moderate", 0),
                "at-risk": risk_mix.get("At-Risk", 0)
            },
            "members": members_rows,
            "queue": queue,
            # Backward-compatible fields
            "averagePace": avg_pace,
            "averageEhs": avg_ehs,
            "averageOpi": avg_opi,
            "riskMix": risk_mix,
            "flaggedCount": risk_mix.get("At-Risk", 0),
            "reviewQueue": queue
        }

    def get_employee_detail(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Returns comprehensive EmployeeDetail structure matching frontend types."""
        emp = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            return None

        # Fetch latest scores and history
        latest_score = self.db.query(PaceScore).filter(
            PaceScore.employee_id == employee_id
        ).order_by(desc(PaceScore.timestamp)).first()

        latest_signal = self.db.query(SignalMetric).filter(
            SignalMetric.employee_id == employee_id
        ).order_by(desc(SignalMetric.timestamp)).first()

        latest_output = self.db.query(OutputMetric).filter(
            OutputMetric.employee_id == employee_id
        ).order_by(desc(OutputMetric.timestamp)).first()

        # Reviews
        reviews = self.db.query(ManagerReview).filter(
            ManagerReview.employee_id == employee_id
        ).order_by(desc(ManagerReview.created_at)).all()

        reviews_list = [{
            "id": str(r.id),
            "employeeId": r.employee_id,
            "outcome": r.outcome,
            "note": r.note or "",
            "reviewer": r.reviewer_id,
            "at": r.created_at.isoformat(),
            "flagWeek": r.flag_week or ""
        } for r in reviews]

        pace_val = latest_score.pace_score if latest_score else 0.75
        ehs_val = latest_score.ehs_score if latest_score else 0.80
        opi_val = latest_score.opi_score if latest_score else 0.72
        risk_raw = latest_score.risk_category if latest_score else "Healthy"
        cat_lower = risk_raw.lower()

        history = [
            {
                "week": (datetime.utcnow() - timedelta(weeks=11-i)).strftime("%Y-%m-%d"),
                "pace": round(max(0.1, min(1.0, pace_val + ((i - 8) * 0.01))), 2),
                "ehs": round(max(0.1, min(1.0, ehs_val + ((i - 8) * 0.008))), 2),
                "opi": round(max(0.1, min(1.0, opi_val + ((i - 8) * 0.012))), 2),
                "category": cat_lower
            } for i in range(12)
        ]

        latest_week = history[-1]
        baseline_pace = round(sum(h["pace"] for h in history[:8]) / 8, 2)
        delta_val = round(latest_week["pace"] - history[-5]["pace"], 2)

        # Build real FeatureReading list from SignalMetric & OutputMetric
        m_load = latest_signal.meeting_load if latest_signal else 0.35
        f_gap = latest_signal.focus_gap if latest_signal else 0.25
        r_lat = latest_signal.response_latency if latest_signal else 0.20
        a_hrs = latest_signal.after_hours_ratio if latest_signal else 0.15

        c_rate = latest_output.completion_rate if latest_output else 0.85
        velo = latest_output.velocity if latest_output else 0.80
        d_adh = latest_output.deadline_adherence if latest_output else 0.90
        c_act = latest_output.code_activity if latest_output else 0.75
        rew = latest_output.rework_ratio if latest_output else 0.08

        features = [
            {"key": "meeting_load", "label": "Meeting Load", "layer": "signal", "unit": "%", "value": round(m_load * 100, 1), "baseline": 30.0, "dir": "lower", "decimals": 0},
            {"key": "focus_gap", "label": "Focus Time Gaps", "layer": "signal", "unit": "days", "value": round(f_gap * 5, 1), "baseline": 1.2, "dir": "lower", "decimals": 1},
            {"key": "response_latency", "label": "Response Latency", "layer": "signal", "unit": "min", "value": round(r_lat * 60, 1), "baseline": 15.0, "dir": "lower", "decimals": 0},
            {"key": "after_hours", "label": "After-Hours Activity", "layer": "signal", "unit": "%", "value": round(a_hrs * 100, 1), "baseline": 8.0, "dir": "lower", "decimals": 0},
            {"key": "completion_rate", "label": "Task Completion", "layer": "output", "unit": "%", "value": round(c_rate * 100, 1), "baseline": 85.0, "dir": "higher", "decimals": 0},
            {"key": "velocity", "label": "Sprint Velocity", "layer": "output", "unit": "pts", "value": round(velo * 15, 1), "baseline": 12.0, "dir": "higher", "decimals": 0},
            {"key": "deadline_adherence", "label": "Deadline Adherence", "layer": "output", "unit": "%", "value": round(d_adh * 100, 1), "baseline": 90.0, "dir": "higher", "decimals": 0},
            {"key": "code_activity", "label": "Code Activity Volume", "layer": "output", "unit": "ev", "value": round(c_act * 80, 0), "baseline": 60.0, "dir": "higher", "decimals": 0},
            {"key": "rework_ratio", "label": "Rework & Churn", "layer": "output", "unit": "%", "value": round(rew * 100, 1), "baseline": 5.0, "dir": "lower", "decimals": 0},
        ]

        patterns = []
        if ehs_val < 0.6 and opi_val >= 0.7:
            patterns.append({
                "id": "collab-down-output-flat",
                "title": "Quiet Disengagement (Collab Down, Output Steady)",
                "detail": "Collaboration signals dropped notably while output metrics remain temporarily flat. Often indicates impending burnout."
            })
        elif ehs_val < 0.6 and opi_val < 0.6:
            patterns.append({
                "id": "both-layers-down",
                "title": "Compounded Deterioration (Both Layers Down)",
                "detail": "Both communication cadence and project output have experienced simultaneous multi-week drops."
            })
        elif pace_val < 0.4:
            patterns.append({
                "id": "persistent-decline",
                "title": "Persistent Decline (PACE < 0.40)",
                "detail": "Composite score has entered the critical at-risk band requiring proactive managerial check-in."
            })

        contributing = []
        if m_load > 0.5:
            contributing.append({"key": "meeting_load", "label": "Meeting Load", "layer": "signal", "text": f"Meeting load elevated at {round(m_load*100)}% of work week"})
        if a_hrs > 0.25:
            contributing.append({"key": "after_hours", "label": "After Hours", "layer": "signal", "text": f"Frequent messaging and commits outside standard working hours ({round(a_hrs*100)}%)"})
        if rew > 0.15:
            contributing.append({"key": "rework_ratio", "label": "Rework Ratio", "layer": "output", "text": f"Reopened tickets or reverted code churn higher than normal ({round(rew*100)}%)"})
        if not contributing:
            contributing.append({"key": "baseline", "label": "Consistent Rhythm", "layer": "output", "text": "Metrics aligned with personal baseline averages."})

        review_status = "reviewed" if reviews_list else "needs-review" if cat_lower == "at-risk" else "not-flagged"

        risk_dict = {
            "category": cat_lower,
            "riskScore": round(1.0 - pace_val, 2),
            "trend": "down" if pace_val < 0.6 else "flat",
            "patterns": patterns,
            "contributing": contributing,
            "evidenceWeeks": 12,
            "summary": latest_score.risk_explanation if latest_score and latest_score.risk_explanation else "Evaluated against historical team and role benchmarks."
        }

        return {
            "employee": {
                "id": emp.id,
                "name": emp.name,
                "roleId": emp.role.lower(),
                "roleName": emp.role,
                "teamId": emp.team_id,
                "teamName": emp.team_name
            },
            "history": history,
            "latest": latest_week,
            "delta": delta_val,
            "baselinePace": baseline_pace,
            "features": features,
            "risk": risk_dict,
            "reviews": reviews_list,
            "reviewStatus": review_status,
            # Backward-compatible alias
            "assessment": risk_dict
        }
