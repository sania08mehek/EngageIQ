"""
EngageIQ Data Pipeline - Database Session & Initialization
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sys
from pathlib import Path

# Add pipeline root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import config

# Database engine
connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(config.DATABASE_URL, connect_args=connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes all database tables."""
    import database.models  # Ensure models are imported
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized with schema at: {config.DATABASE_URL}")
