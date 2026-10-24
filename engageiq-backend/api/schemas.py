"""
EngageIQ Data Pipeline - API Schemas (Pydantic Models)
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ReviewInputSchema(BaseModel):
    outcome: str = Field(..., description="Review outcome type (e.g., discuss-workload, check-blockers, no-concern)")
    note: str = Field("", description="Manager's contextual notes")


class ReviewRecordSchema(BaseModel):
    id: str
    employeeId: str
    outcome: str
    note: str
    reviewer: str
    at: str
    flagWeek: str


class ScoreRecordSchema(BaseModel):
    id: int
    employee_id: str
    employee_name: str
    role: str
    team_id: str
    team_name: str
    ehs: float
    opi: float
    pace: float
    risk: str
    risk_explanation: Optional[str] = None
    timestamp: str


class PipelineRunResponse(BaseModel):
    status: str
    run_id: str
    total_records: int
    processed_records: int
    risk_events_created: int
    data: List[Dict[str, Any]]
    message: str


class RiskEventSchema(BaseModel):
    id: int
    employee_id: str
    risk_type: str
    severity: str
    evidence: str
    status: str
    detected_at: str
