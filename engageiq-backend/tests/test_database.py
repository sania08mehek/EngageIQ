"""
Tests for Relational Database Persistence & Repository
"""

import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Add pipeline root to path
PIPELINE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_ROOT))

from database.db_session import Base
from database.models import Employee, PaceScore, ManagerReview
from database.repository import PipelineRepository


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_repository_upsert_and_store(in_memory_db):
    repo = PipelineRepository(in_memory_db)
    
    # Create test scored dataframe
    df = pd.DataFrame({
        "employee_id": ["TEST-001"],
        "employee_name": ["Jane Doe"],
        "role": ["Engineer"],
        "team_id": ["core"],
        "team_name": ["Core Backend"],
        "meeting_load": [0.2],
        "focus_gap": [0.2],
        "response_latency": [0.1],
        "after_hours_ratio": [0.1],
        "completion_rate": [0.9],
        "velocity": [1.0],
        "deadline_adherence": [0.95],
        "code_activity": [0.8],
        "rework_ratio": [0.05],
        "ehs_score": [0.85],
        "opi_score": [0.82],
        "pace_score": [0.83],
        "risk_category": ["Healthy"],
        "risk_explanation": ["EHS: 0.85 (40%), OPI: 0.82 (60%)"]
    })

    count = repo.store_pipeline_batch(df)
    assert count == 1

    emp = in_memory_db.query(Employee).filter_by(id="TEST-001").first()
    assert emp is not None
    assert emp.name == "Jane Doe"

    score = in_memory_db.query(PaceScore).filter_by(employee_id="TEST-001").first()
    assert score is not None
    assert score.pace_score == 0.83


def test_store_manager_review(in_memory_db):
    repo = PipelineRepository(in_memory_db)
    repo.upsert_employee("TEST-002", "John Smith", "Manager", "platform", "Platform")
    
    review = repo.store_review(
        employee_id="TEST-002",
        outcome="discuss-workload",
        note="Follow up next sprint regarding high meeting load."
    )

    assert review.id is not None
    assert review.outcome == "discuss-workload"
