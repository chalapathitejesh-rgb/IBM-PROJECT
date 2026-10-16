from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import database, models
from ..api import auth
from ..worker.tasks import process_email
import hashlib

router = APIRouter()

class EmailUploadRequest(BaseModel):
    case_id: int
    sender_email: str
    subject: str
    body: str
    has_attachments: bool = False

@router.post("/analyze")
def analyze_email(
    request: EmailUploadRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    case = db.query(models.Case).filter(models.Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Create a hash of the email content to use as file_hash
    content = f"{request.sender_email}|{request.subject}|{request.body}".encode('utf-8')
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Store email metadata as an Evidence Record (text-based evidence)
    evidence = models.Evidence(
        case_id=request.case_id,
        filename=f"email_{file_hash[:8]}.txt",
        file_hash=file_hash,
        file_path="", # No file path for direct text upload
        uploader_id=current_user.id
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    
    # Audit Log
    log = models.AuditLog(
        user_id=current_user.id,
        action="ANALYZE_EMAIL_EVIDENCE",
        target_type="evidence",
        target_id=evidence.id
    )
    db.add(log)
    db.commit()
    
    # Immediate ML inference for instant results
    from ..ml.email.pipeline import EmailPipeline
    email_pipe = EmailPipeline(device='cpu')
    res = email_pipe.analyze_email(request.sender_email, request.subject, request.body, request.has_attachments)
    prob = res["final_phishing_probability"]
    label = "Phishing" if prob > 0.5 else "Legitimate"
    
    prediction = models.Prediction(
        evidence_id=evidence.id,
        module="email",
        model_name="DistilBERT-Phishing",
        model_version="1.0",
        dataset_version="Enron+Phishing",
        prediction_label=label,
        confidence=prob if label == "Phishing" else (1 - prob),
        processing_time_ms=50
    )
    db.add(prediction)
    db.commit()
    
    task_id = None
    try:
        task = process_email.delay(
            evidence.id, 
            request.sender_email, 
            request.subject, 
            request.body, 
            request.has_attachments
        )
        task_id = task.id
    except Exception as e:
        print(f"Celery task dispatch skipped: {e}")
    
    return {
        "message": "Email analyzed successfully.",
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
        .filter(models.Prediction.module == "email").first()
        
    if not prediction:
        raise HTTPException(status_code=404, detail="Results not found or still processing.")
        
    return prediction
