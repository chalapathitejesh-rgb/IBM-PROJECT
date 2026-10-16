from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import database, models
from ..api import auth
from ..worker.tasks import process_url
import hashlib

router = APIRouter()

class URLUploadRequest(BaseModel):
    case_id: int
    url: str

@router.post("/scan")
def scan_url(
    request: URLUploadRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    case = db.query(models.Case).filter(models.Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Create a hash of the URL to use as file_hash
    content = request.url.encode('utf-8')
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Store URL as an Evidence Record
    evidence = models.Evidence(
        case_id=request.case_id,
        filename=f"url_{file_hash[:8]}.txt",
        file_hash=file_hash,
        file_path=request.url, # We store the actual URL here since there's no file
        uploader_id=current_user.id
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    
    # Audit Log
    log = models.AuditLog(
        user_id=current_user.id,
        action="SCAN_URL_EVIDENCE",
        target_type="evidence",
        target_id=evidence.id
    )
    db.add(log)
    db.commit()
    
    # Immediate ML inference for instant results
    from ..ml.url.pipeline import URLPipeline
    url_pipe = URLPipeline()
    res = url_pipe.analyze_url(request.url)
    prob = res["malicious_probability"]
    label = "Malicious" if prob > 0.5 else "Benign"
    
    prediction = models.Prediction(
        evidence_id=evidence.id,
        module="url",
        model_name="RandomForest-Lexical",
        model_version="1.0",
        dataset_version="PhishTank+Alexa",
        prediction_label=label,
        confidence=prob if label == "Malicious" else (1 - prob),
        processing_time_ms=10
    )
    db.add(prediction)
    db.commit()
    
    # Also queue Celery task if worker is listening
    task_id = None
    try:
        task = process_url.delay(evidence.id, request.url)
        task_id = task.id
    except Exception as e:
        print(f"Celery task dispatch skipped: {e}")
    
    return {
        "message": "URL scanned successfully.",
        "evidence_id": evidence.id,
        "prediction": {"label": label, "confidence": prob},
        "task_id": task_id
    }

@router.get("/results/{evidence_id}")
def get_results(
    evidence_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    prediction = db.query(models.Prediction)\
        .filter(models.Prediction.evidence_id == evidence_id)\
        .filter(models.Prediction.module == "url").first()
        
    if not prediction:
        raise HTTPException(status_code=404, detail="Results not found or still processing.")
        
    return prediction
