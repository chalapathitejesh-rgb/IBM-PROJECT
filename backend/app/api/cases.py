from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional, Any
from ..db import database, models
from ..api import auth

router = APIRouter()

class CaseCreate(BaseModel):
    title: str
    description: str

class CaseResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/stats/overview")
def get_soc_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Computes real, live database metrics across all cases and evidence modules.
    No static mock data.
    """
    total_cases = db.query(models.Case).count()
    open_cases = db.query(models.Case).filter(models.Case.status.in_(["open", "investigating"])).count()
    resolved_cases = db.query(models.Case).filter(models.Case.status == "closed").count()
    
    total_evidence = db.query(models.Evidence).count()
    
    # Real counts per ML module from predictions table
    deepfake_scans = db.query(models.Prediction).filter(models.Prediction.module == "deepfake").count()
    voice_scans = db.query(models.Prediction).filter(models.Prediction.module == "voice").count()
    email_scans = db.query(models.Prediction).filter(models.Prediction.module == "email").count()
    url_scans = db.query(models.Prediction).filter(models.Prediction.module == "url").count()
    network_scans = db.query(models.Prediction).filter(models.Prediction.module == "network").count()
    
    # Threats detected (count where label is malicious/anomalous/fake)
    threat_labels = ["Fake", "Phishing", "Malicious", "Anomalous", "Synthetic"]
    detected_threats = db.query(models.Prediction).filter(models.Prediction.prediction_label.in_(threat_labels)).count()
    
    # Average processing time
    avg_latency = db.query(func.avg(models.Prediction.processing_time_ms)).scalar() or 0
    
    return {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "resolved_cases": resolved_cases,
        "total_evidence": total_evidence,
        "deepfake_scans": deepfake_scans,
        "voice_scans": voice_scans,
        "email_scans": email_scans,
        "url_scans": url_scans,
        "network_scans": network_scans,
        "detected_threats": detected_threats,
        "avg_latency_ms": round(float(avg_latency), 1)
    }

@router.get("/")
def list_cases(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    cases = db.query(models.Case).order_by(models.Case.id.desc()).all()
    results = []
    for c in cases:
        evidence_count = db.query(models.Evidence).filter(models.Evidence.case_id == c.id).count()
        results.append({
            "id": c.id,
            "title": c.title,
            "description": c.description,
            "status": c.status,
            "evidence_count": evidence_count,
            "created_at": str(c.created_at) if c.created_at else None
        })
    return results

@router.post("/")
def create_case(
    case_data: CaseCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    new_case = models.Case(
        title=case_data.title,
        description=case_data.description,
        created_by=current_user.id
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    
    # Audit log
    log = models.AuditLog(
        user_id=current_user.id,
        action="CREATE_CASE",
        target_type="case",
        target_id=new_case.id
    )
    db.add(log)
    db.commit()
    
    return {
        "id": new_case.id,
        "title": new_case.title,
        "description": new_case.description,
        "status": new_case.status,
        "created_at": str(new_case.created_at) if new_case.created_at else None
    }

@router.get("/{case_id}")
def get_case(
    case_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    evidence_records = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).order_by(models.Evidence.id.desc()).all()
    
    evidence_list = []
    for e in evidence_records:
        preds = db.query(models.Prediction).filter(models.Prediction.evidence_id == e.id).all()
        pred_list = []
        for p in preds:
            pred_list.append({
                "id": p.id,
                "module": p.module,
                "model_name": p.model_name,
                "model_version": p.model_version,
                "dataset_version": p.dataset_version,
                "prediction_label": p.prediction_label,
                "confidence": round(float(p.confidence) * 100, 1),
                "processing_time_ms": p.processing_time_ms,
                "created_at": str(p.created_at) if p.created_at else None
            })
        
        evidence_list.append({
            "id": e.id,
            "filename": e.filename,
            "file_hash": e.file_hash,
            "file_path": e.file_path,
            "uploaded_at": str(e.uploaded_at) if e.uploaded_at else None,
            "predictions": pred_list
        })
    
    return {
        "case": {
            "id": case.id,
            "title": case.title,
            "description": case.description,
            "status": case.status,
            "created_at": str(case.created_at) if case.created_at else None
        },
        "evidence": evidence_list
    }
