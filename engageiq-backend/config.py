"""
EngageIQ Data Pipeline - Configuration
Centralized configuration settings for the pipeline, scoring weights, and database.
"""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Dict


class PipelineConfig(BaseSettings):
    # Base paths
    PIPELINE_ROOT: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = Path(__file__).resolve().parent / "uploads"
    OUTPUT_DIR: Path = Path(__file__).resolve().parent / "output"
    
    # Relational Database URL (SQLite default, can be switched to PostgreSQL)
    DATABASE_URL: str = f"sqlite:///{Path(__file__).resolve().parent}/engageiq.db"
    
    # FastAPI Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Vite React dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]
    
    # 40:60 PACE Weights
    EHS_WEIGHT: float = 0.40
    OPI_WEIGHT: float = 0.60
    
    # EHS Weights (Signal metrics)
    W_MEETING_LOAD: float = 0.30
    W_FOCUS_GAP: float = 0.30
    W_RESPONSE_LATENCY: float = 0.20
    W_AFTER_HOURS: float = 0.20
    
    # OPI Weights (Output metrics)
    W_TASK_COMPLETION: float = 0.25
    W_VELOCITY: float = 0.25
    W_DEADLINE_ADHERENCE: float = 0.20
    W_ACTIVITY: float = 0.20
    W_REWORK_PENALTY: float = 0.10
    
    # Risk Thresholds
    HEALTHY_THRESHOLD: float = 0.70
    MODERATE_THRESHOLD: float = 0.40
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = PipelineConfig()

# Ensure directories exist
config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
