from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pandas as pd
import io

from database import engine, Base, get_db
import models
from pace_engine import compute_ehs, compute_opi, compute_pace, classify_risk

# Create db tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EngageIQ API")

# Allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "PACE Engine Backend is running"}

@app.post("/api/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    contents = await file.read()
    try:
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
        
    required_cols = [
        "employee_id", "employee_name", 
        "meeting_load", "focus_gap", "response_latency", "after_hours_ratio",
        "completion_rate", "velocity", "deadline_adherence", "code_activity", "rework_ratio"
    ]
    
    for col in required_cols:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing required column: {col}")

    processed_records = []
    
    for index, row in df.iterrows():
        # Get or create employee
        emp = db.query(models.Employee).filter(models.Employee.id == row['employee_id']).first()
        if not emp:
            emp = models.Employee(id=row['employee_id'], name=row['employee_name'], role="Engineer")
            db.add(emp)
            db.commit()
            db.refresh(emp)
            
        # Compute scores
        ehs = compute_ehs(row['meeting_load'], row['focus_gap'], row['response_latency'], row['after_hours_ratio'])
        opi = compute_opi(row['completion_rate'], row['velocity'], row['deadline_adherence'], row['code_activity'], row['rework_ratio'])
        pace = compute_pace(ehs, opi)
        risk = classify_risk(pace)
        
        # Save score
        score_record = models.PaceScore(
            employee_id=emp.id,
            ehs_score=ehs,
            opi_score=opi,
            pace_score=pace,
            risk_category=risk,
            risk_explanation=f"EHS: {ehs:.2f}, OPI: {opi:.2f}"
        )
        db.add(score_record)
        processed_records.append({
            "employee": emp.name,
            "pace": pace,
            "risk": risk
        })
        
    db.commit()
    
    return {"status": "success", "processed_records": len(processed_records), "data": processed_records}

@app.get("/api/scores")
def get_scores(db: Session = Depends(get_db)):
    scores = db.query(models.PaceScore).all()
    results = []
    for s in scores:
        results.append({
            "id": s.id,
            "employee_id": s.employee_id,
            "employee_name": s.employee.name if s.employee else "Unknown",
            "ehs": s.ehs_score,
            "opi": s.opi_score,
            "pace": s.pace_score,
            "risk": s.risk_category,
            "explanation": s.risk_explanation,
            "timestamp": s.timestamp
        })
    return results
