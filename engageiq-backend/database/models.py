"""
EngageIQ Data Pipeline - SQLAlchemy Relational Models
Implements tables specified in EngageIQ Master Architecture:
- employees
- signal_metrics
- output_metrics
- pace_scores
- risk_events
- manager_reviews
- pipeline_runs
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from .db_session import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    role = Column(String, default="Engineer")
    team_id = Column(String, index=True, default="platform")
    team_name = Column(String, default="Platform Engineering")
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    signal_metrics = relationship("SignalMetric", back_populates="employee", cascade="all, delete-orphan")
    output_metrics = relationship("OutputMetric", back_populates="employee", cascade="all, delete-orphan")
    pace_scores = relationship("PaceScore", back_populates="employee", cascade="all, delete-orphan")
    risk_events = relationship("RiskEvent", back_populates="employee", cascade="all, delete-orphan")
    reviews = relationship("ManagerReview", back_populates="employee", cascade="all, delete-orphan")


class SignalMetric(Base):
    """Signal layer features (EHS inputs & score)."""
    __tablename__ = "signal_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Normalized load [0, 1]
    meeting_load = Column(Float)
    focus_gap = Column(Float)
    response_latency = Column(Float)
    after_hours_ratio = Column(Float)

    # Raw metrics (if available)
    meeting_hours = Column(Float, nullable=True)
    focus_gap_days = Column(Float, nullable=True)
    response_latency_hours = Column(Float, nullable=True)
    after_hours_pct = Column(Float, nullable=True)

    ehs_score = Column(Float)

    employee = relationship("Employee", back_populates="signal_metrics")


class OutputMetric(Base):
    """Output layer features (OPI inputs & score)."""
    __tablename__ = "output_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    completion_rate = Column(Float)
    velocity = Column(Float)
    deadline_adherence = Column(Float)
    code_activity = Column(Float)
    rework_ratio = Column(Float)

    opi_score = Column(Float)

    employee = relationship("Employee", back_populates="output_metrics")


class PaceScore(Base):
    """Calculated 40:60 PACE score and risk classification."""
    __tablename__ = "pace_scores"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    ehs_score = Column(Float, nullable=False)
    opi_score = Column(Float, nullable=False)
    pace_score = Column(Float, nullable=False)

    risk_category = Column(String, default="Healthy")  # Healthy, Moderate, At-Risk
    risk_explanation = Column(String)

    employee = relationship("Employee", back_populates="pace_scores")


class RiskEvent(Base):
    """Detected risk patterns and anomalies."""
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True, nullable=False)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)

    risk_type = Column(String, nullable=False)  # collab-down-output-flat, both-layers-down, persistent-decline
    severity = Column(String, default="medium")  # low, medium, high, critical
    evidence = Column(Text)  # JSON or text evidence description
    status = Column(String, default="open")  # open, under_review, resolved, dismissed

    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="risk_events")


class ManagerReview(Base):
    """Human-in-the-loop contextual reviews submitted by managers."""
    __tablename__ = "manager_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(String, ForeignKey("employees.id"), index=True, nullable=False)
    reviewer_id = Column(String, default="manager")
    review_date = Column(DateTime, default=datetime.datetime.utcnow)

    outcome = Column(String, nullable=False)  # no-concern, monitor-trend, discuss-workload, check-blockers, offer-support, correct-data, override-signal
    note = Column(Text, nullable=True)
    flag_week = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    employee = relationship("Employee", back_populates="reviews")


class PipelineRun(Base):
    """Audit log of pipeline executions."""
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String, unique=True, index=True, nullable=False)
    source_file = Column(String)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    risk_events_count = Column(Integer, default=0)
    status = Column(String, default="running")  # running, success, failed
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
