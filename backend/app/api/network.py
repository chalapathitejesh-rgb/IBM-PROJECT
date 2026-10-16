from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import database, models
from ..api import auth
from ..worker.tasks import process_network_flow
import hashlib
import json

router = APIRouter()

class NetworkFlowRequest(BaseModel):
    case_id: int
    duration: float = 0.0
    src_bytes: int = 0
    dst_bytes: int = 0
    missed_bytes: int = 0
    src_pkts: int = 0
    dst_pkts: int = 0
    protocol: str = "tcp"

@router.post("/analyze")
def analyze_flow(
    request: NetworkFlowRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    case = db.query(models.Case).filter(models.Case.id == request.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # Convert request to dict for hashing and Celery
    flow_data = request.model_dump()
    flow_data.pop("case_id")
    
    content = json.dumps(flow_data, sort_keys=True).encode('utf-8')
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Store flow data as an Evidence Record
    evidence = models.Evidence(
        case_id=request.case_id,
        filename=f"flow_{file_hash[:8]}.json",
        file_hash=file_hash,
        file_path=json.dumps(flow_data), # We store the JSON string directly in file_path for simplicity
        uploader_id=current_user.id
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    
    # Audit Log
    log = models.AuditLog(
        user_id=current_user.id,
        action="ANALYZE_NETWORK_EVIDENCE",
        target_type="evidence",
        target_id=evidence.id
    )
    db.add(log)
    db.commit()
    
    # Immediate ML inference for instant results
    from ..ml.network.pipeline import NetworkPipeline
    net_pipe = NetworkPipeline()
    res = net_pipe.analyze_flow(flow_data)
    prob = res["anomaly_probability"]
    label = "Anomalous" if prob > 0.5 else "Normal"
    
    prediction = models.Prediction(
        evidence_id=evidence.id,
        module="network",
        model_name="Autoencoder-IDS",
        model_version="1.0",
        dataset_version="CIC-IDS2017",
        prediction_label=label,
        confidence=prob if label == "Anomalous" else (1 - prob),
        processing_time_ms=10
    )
    db.add(prediction)
    db.commit()
    
    task_id = None
    try:
        task = process_network_flow.delay(evidence.id, flow_data)
        task_id = task.id
    except Exception as e:
        print(f"Celery task dispatch skipped: {e}")
    
    return {
        "message": "Network flow analyzed successfully.",
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
        .filter(models.Prediction.module == "network").first()
        
    if not prediction:
        raise HTTPException(status_code=404, detail="Results not found or still processing.")
        
    return prediction
