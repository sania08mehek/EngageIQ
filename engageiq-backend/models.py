from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)
    team = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PaceScore(Base):
    __tablename__ = "pace_scores"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    ehs_score = Column(Float)
    opi_score = Column(Float)
    pace_score = Column(Float)
    
    risk_category = Column(String) # Healthy, Moderate, At-Risk
    risk_explanation = Column(String)
    
    employee = relationship("Employee")
