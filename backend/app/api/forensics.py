from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import database, models
from ..api import auth

router = APIRouter()

@router.get("/case/{case_id}/chain-of-custody")
def get_chain_of_custody(
    case_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """
    Fetches the forensic Chain of Custody (Audit Logs) for a specific case.
    This tracks exactly who uploaded evidence, who analyzed it, and when.
    """
    case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    # 1. Get all evidence for this case
    evidence_list = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()
    evidence_ids = [e.id for e in evidence_list]

    # 2. Fetch Audit Logs for the Case itself and any Evidence belonging to it
    logs = db.query(models.AuditLog).filter(
        (models.AuditLog.target_type == "case") & (models.AuditLog.target_id == case_id) |
        (models.AuditLog.target_type == "evidence") & (models.AuditLog.target_id.in_(evidence_ids))
    ).order_by(models.AuditLog.timestamp.desc()).all()

    # 3. Format the response
    chain = []
    for log in logs:
        user = db.query(models.User).filter(models.User.id == log.user_id).first()
        chain.append({
            "timestamp": str(log.timestamp) if log.timestamp else None,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "user": user.email if user else "Unknown User"
        })

    return {
        "case_id": case_id,
        "title": case.title,
        "total_events": len(chain),
        "chain_of_custody": chain
    }
