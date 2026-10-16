from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import database, models
from ..api import auth
from ..worker.tasks import process_risk_fusion

router = APIRouter()

@router.post("/aggregate/{case_id}")
def trigger_fusion(
    case_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Calculates overall HTCS risk score for all evidence in the specified case.
    """
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Audit Log
    log = models.AuditLog(
        user_id=current_user.id,
        action="TRIGGER_RISK_FUSION",
        target_type="case",
        target_id=case_id
    )
    db.add(log)
    db.commit()
    
    # Calculate score directly
    evidence_list = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    evidence_ids = [e.id for e in evidence_list]
    predictions = db.query(models.Prediction).filter(models.Prediction.evidence_id.in_(evidence_ids)).all()
    
    from ..ml.fusion.pipeline import RiskFusionPipeline
    pipeline = RiskFusionPipeline()
    
    pred_dicts = []
    for p in predictions:
        pred_dicts.append({
            "module": p.module,
            "prediction_label": p.prediction_label,
            "confidence": p.confidence
        })
        
    result = pipeline.fuse_risks(pred_dicts)
    
    # Try queuing Celery background aggregation
    task_id = None
    try:
        task = process_risk_fusion.delay(case_id)
        task_id = task.id
    except Exception as e:
        print(f"Celery task dispatch skipped: {e}")
    
    return {
        "message": "Risk Fusion calculated successfully.",
        "case_id": case_id,
        "score": result,
        "task_id": task_id
    }

@router.get("/score/{case_id}")
def get_live_score(
    case_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Synchronously calculates the risk score on-the-fly for immediate frontend display.
    """
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
        
    evidence_list = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    evidence_ids = [e.id for e in evidence_list]
    
    predictions = db.query(models.Prediction).filter(models.Prediction.evidence_id.in_(evidence_ids)).all()
    
    from ..ml.fusion.pipeline import RiskFusionPipeline
    pipeline = RiskFusionPipeline()
    
    pred_dicts = []
    for p in predictions:
        pred_dicts.append({
            "module": p.module,
            "prediction_label": p.prediction_label,
            "confidence": p.confidence
        })
        
    result = pipeline.fuse_risks(pred_dicts)
    
    return result
