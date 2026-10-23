"""
EngageIQ Data Pipeline - FastAPI Server
Exposes the data pipeline endpoints and connects directly to the React Dashboard.
"""

import sys
import io
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

# Add pipeline root to path
PIPELINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_ROOT))

from config import config
from database.db_session import get_db, init_db, engine
from database.repository import PipelineRepository
from database.models import PipelineRun, RiskEvent
from preprocessing.validator import DataValidator
from preprocessing.cleaner import DataCleaner
from preprocessing.normalizer import RoleAwareNormalizer
from scoring.pace_engine import PACEEngine
from scoring.pattern_detector import PatternDetector
from api.schemas import ReviewInputSchema, ReviewRecordSchema, ScoreRecordSchema, PipelineRunResponse
from integration.webhook_router import router as integration_router

# Initialize database schema
init_db()

app = FastAPI(
    title="EngageIQ Data Pipeline API",
    description="Production-grade data pipeline for employee engagement (EHS) and performance (OPI) scoring with 40:60 PACE formula.",
    version="2.0.0",
)

# Mount Integration & Webhook Router
app.include_router(integration_router)

# CORS middleware to allow React frontend (Vite & Create React App)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared pipeline components
validator = DataValidator(strict_bounds=False)
cleaner = DataCleaner()
normalizer = RoleAwareNormalizer()
pace_engine = PACEEngine(ehs_weight=config.EHS_WEIGHT, opi_weight=config.OPI_WEIGHT)
pattern_detector = PatternDetector()


# ─── CORE PIPELINE EXECUTION FUNCTION ───────────────────────────────────────

def execute_pipeline(df: pd.DataFrame, source_filename: str, db: Session) -> Dict[str, Any]:
    """
    Executes the 5-step data pipeline:
    1. Validation
    2. Cleaning
    3. Role-aware Normalization
    4. EHS & OPI Calculation -> 40:60 PACE Score
    5. Database Storage (metrics, scores, risk events)
    """
    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    started_at = datetime.utcnow()

    # Track pipeline run
    pipeline_run = PipelineRun(
        run_id=run_id,
        source_file=source_filename,
        total_records=len(df),
        status="running",
        started_at=started_at
    )
    db.add(pipeline_run)
    db.commit()

    try:
        # Step 1: Validation
        valid_df, invalid_df, val_result = validator.validate_dataframe(df)
        if not val_result.is_valid and len(valid_df) == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {val_result.errors[0]['message'] if val_result.errors else 'Unknown error'}"
            )

        # Step 2: Cleaning & Imputation
        cleaned_df = cleaner.clean_dataframe(valid_df)

        # Step 3: Role-Aware Normalization
        normalized_df = normalizer.normalize_dataframe(cleaned_df)

        # Step 4: Scoring (EHS, OPI, 40:60 PACE)
        scored_df = pace_engine.process_dataframe(normalized_df)

        # Step 5: Risk Pattern Detection
        detected_risks = pattern_detector.detect_patterns(scored_df)

        # Step 6: Relational Database Persistence
        repo = PipelineRepository(db)
        stored_count = repo.store_pipeline_batch(scored_df, detected_risks)

        # Update pipeline run status
        pipeline_run.processed_records = stored_count
        pipeline_run.risk_events_count = len(detected_risks)
        pipeline_run.status = "success"
        pipeline_run.completed_at = datetime.utcnow()
        db.commit()

        # Build output preview
        preview_data = []
        for _, row in scored_df.iterrows():
            preview_data.append({
                "employee_id": row["employee_id"],
                "employee": row["employee_name"],
                "role": row["role"],
                "team": row["team_id"],
                "ehs": round(float(row["ehs_score"]), 2),
                "opi": round(float(row["opi_score"]), 2),
                "pace": round(float(row["pace_score"]), 2),
                "risk": row["risk_category"]
            })

        return {
            "status": "success",
            "run_id": run_id,
            "total_records": len(df),
            "processed_records": stored_count,
            "risk_events_created": len(detected_risks),
            "data": preview_data,
            "message": f"Successfully processed {stored_count} records through the PACE pipeline."
        }

    except Exception as e:
        pipeline_run.status = "failed"
        pipeline_run.error_message = str(e)
        pipeline_run.completed_at = datetime.utcnow()
        db.commit()
        raise e


# ─── API ENDPOINTS ──────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "service": "EngageIQ Data Pipeline API",
        "status": "online",
        "engine": "PACE 40:60 Linear Scoring Engine",
        "database": config.DATABASE_URL
    }


# ─── PIPELINE INGESTION ENDPOINTS ───────────────────────────────────────────

@app.post("/api/upload")
@app.post("/api/pipeline/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts CSV uploads from the React dashboard or external pipelines.
    Supports both /api/upload (standard EngageIQ frontend route) and /api/pipeline/upload.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(io.StringIO(contents.decode("latin-1")))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    result = execute_pipeline(df, source_filename=file.filename, db=db)
    return result


@app.post("/api/pipeline/run-sample")
def run_sample_pipeline(db: Session = Depends(get_db)):
    """
    Loads and processes the pre-bundled sample dataset (employees_sample.csv).
    Useful for quick testing or onboarding.
    """
    sample_path = PIPELINE_ROOT / "dataset" / "employees_sample.csv"
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail="Sample dataset file not found.")

    df = pd.read_csv(sample_path)
    result = execute_pipeline(df, source_filename="employees_sample.csv", db=db)
    return result


# ─── FRONTEND DASHBOARD CONNECTOR ENDPOINTS ─────────────────────────────────

@app.get("/api/scores")
def get_scores(db: Session = Depends(get_db)):
    """
    Returns latest PACE scores for all employees.
    Directly connected to the React dashboard `fetchRealAndApply()`.
    """
    repo = PipelineRepository(db)
    scores = repo.get_scores_list()
    if not scores:
        # Auto-bootstrap with sample data if empty
        run_sample_pipeline(db)
        scores = repo.get_scores_list()
    return scores


@app.get("/api/organization")
def get_organization(db: Session = Depends(get_db)):
    """
    Returns complete OrgSummary data contract required by React dashboard `api.organization()`.
    """
    repo = PipelineRepository(db)
    summary = repo.get_organization_summary()
    if summary["headcount"] == 0:
        run_sample_pipeline(db)
        summary = repo.get_organization_summary()
    return summary


@app.get("/api/teams/{team_id}")
def get_team(team_id: str, db: Session = Depends(get_db)):
    """
    Returns TeamDetail for the React dashboard `api.team(teamId)`.
    """
    repo = PipelineRepository(db)
    all_scores = repo.get_scores_list()
    team_members = [s for s in all_scores if s["team_id"].lower() == team_id.lower()]

    team_name = team_members[0]["team_name"] if team_members else team_id.title()
    avg_pace = round(sum(s["pace"] for s in team_members) / len(team_members), 2) if team_members else 0.70
    avg_ehs = round(sum(s["ehs"] for s in team_members) / len(team_members), 2) if team_members else 0.70
    avg_opi = round(sum(s["opi"] for s in team_members) / len(team_members), 2) if team_members else 0.70

    risk_mix = {"Healthy": 0, "Moderate": 0, "At-Risk": 0}
    for m in team_members:
        cat = m.get("risk", "Healthy")
        risk_mix[cat] = risk_mix.get(cat, 0) + 1

    members_rows = []
    for m in team_members:
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
                "week": datetime.utcnow().strftime("%Y-W%U"),
                "pace": m["pace"],
                "ehs": m["ehs"],
                "opi": m["opi"],
                "category": m["risk"]
            },
            "delta": -0.02,
            "category": m["risk"],
            "trend": "flat",
            "sparkline": [round(m["pace"] + (i * 0.005), 2) for i in range(8)],
            "flagged": m["risk"] == "At-Risk"
        })

    return {
        "team": {"id": team_id, "name": team_name},
        "headcount": len(team_members),
        "averagePace": avg_pace,
        "averageEhs": avg_ehs,
        "averageOpi": avg_opi,
        "riskMix": risk_mix,
        "flaggedCount": risk_mix.get("At-Risk", 0),
        "members": members_rows,
        "reviewQueue": [m for m in members_rows if m["flagged"]]
    }


@app.get("/api/employees/{employee_id}")
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    """
    Returns full EmployeeDetail for the React dashboard `api.employee(employeeId)`.
    """
    repo = PipelineRepository(db)
    detail = repo.get_employee_detail(employee_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Employee '{employee_id}' not found.")
    return detail


@app.post("/api/employees/{employee_id}/reviews")
def submit_review(employee_id: str, input_data: ReviewInputSchema, db: Session = Depends(get_db)):
    """
    Persists a human review submitted from the React dashboard ReviewPanel.
    Matches POST /api/employees/{employeeId}/reviews expected by frontend.
    """
    repo = PipelineRepository(db)
    rev = repo.store_review(
        employee_id=employee_id,
        outcome=input_data.outcome,
        note=input_data.note
    )
    return {
        "id": str(rev.id),
        "employeeId": rev.employee_id,
        "outcome": rev.outcome,
        "note": rev.note or "",
        "reviewer": rev.reviewer_id,
        "at": rev.created_at.isoformat(),
        "flagWeek": rev.flag_week or datetime.utcnow().strftime("%Y-W%U")
    }


# ─── RISK EVENTS & AUDIT ENDPOINTS ──────────────────────────────────────────

@app.get("/api/pipeline/risk-events")
def get_risk_events(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns detected risk events for active alerting."""
    query = db.query(RiskEvent)
    if status:
        query = query.filter(RiskEvent.status == status)
    events = query.order_by(RiskEvent.detected_at.desc()).limit(100).all()
    
    return [
        {
            "id": e.id,
            "employee_id": e.employee_id,
            "risk_type": e.risk_type,
            "severity": e.severity,
            "evidence": e.evidence,
            "status": e.status,
            "detected_at": e.detected_at.isoformat()
        } for e in events
    ]


@app.get("/api/pipeline/export")
def export_pipeline_results(db: Session = Depends(get_db)):
    """Exports all current employee scores and metrics to CSV."""
    repo = PipelineRepository(db)
    scores = repo.get_scores_list()
    if not scores:
        raise HTTPException(status_code=404, detail="No score records to export.")
    
    df = pd.DataFrame(scores)
    export_path = PIPELINE_ROOT / "output" / "pipeline_export.csv"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(export_path, index=False)
    
    return FileResponse(
        path=str(export_path),
        filename="engageiq_pipeline_export.csv",
        media_type="text/csv"
    )
