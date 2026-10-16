import os
import shutil
from typing import Optional
from celery import shared_task
from sqlalchemy.orm import Session
from ..db.database import SessionLocal
from ..db.models import Evidence, Prediction, Case
from ..ml.deepfake.pipeline import DeepfakePipeline
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global instances to avoid reloading models for every task
deepfake_pipeline: Optional[DeepfakePipeline] = None

def get_deepfake_pipeline():
    global deepfake_pipeline
    if deepfake_pipeline is None:
        logger.info("Initializing Deepfake ML Pipeline...")
        deepfake_pipeline = DeepfakePipeline(device="cpu") # Switch to cuda if GPU is available
    return deepfake_pipeline

@shared_task(bind=True, name="process_deepfake_video")
def process_deepfake_video(self, evidence_id: int):
    db: Session = SessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"status": "error", "message": "Evidence not found"}

        video_path = evidence.file_path
        # Directory to save XAI output
        output_dir = os.path.join(os.path.dirname(video_path), "xai", str(evidence_id))
        
        pipeline = get_deepfake_pipeline()
        
        # Processing the video
        import time
        start_time = time.time()
        result = pipeline.process_video(video_path, output_dir)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("status") == "error":
            return result
            
        probability = result["fake_probability"]
        label = "Fake" if probability > 0.5 else "Real"
        
        # Save prediction to DB
        prediction = Prediction(
            evidence_id=evidence_id,
            module="deepfake",
            model_name="EfficientNet-B4 + ViT Ensemble",
            model_version="1.0",
            dataset_version="FaceForensics++ Base",
            prediction_label=label,
            confidence=probability if label == "Fake" else (1 - probability),
            processing_time_ms=processing_time_ms
        )
        db.add(prediction)
        db.commit()
        
        return {
            "status": "success",
            "fake_probability": probability,
            "heatmaps": result["heatmaps"]
        }
    except Exception as e:
        logger.error(f"Error processing deepfake task: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Global Voice Pipeline
voice_pipeline = None

def get_voice_pipeline():
    global voice_pipeline
    if voice_pipeline is None:
        logger.info("Initializing Voice Clone ML Pipeline...")
        # Local import to prevent circular dependencies if needed
        from ..ml.voice.pipeline import VoicePipeline
        voice_pipeline = VoicePipeline(device="cpu")
    return voice_pipeline

@shared_task(bind=True, name="process_voice_audio")
def process_voice_audio(self, evidence_id: int):
    db: Session = SessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"status": "error", "message": "Evidence not found"}

        audio_path = evidence.file_path
        output_dir = os.path.join(os.path.dirname(audio_path), "xai", str(evidence_id))
        
        pipeline = get_voice_pipeline()
        
        import time
        start_time = time.time()
        result = pipeline.process_audio(audio_path, output_dir)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("status") == "error":
            return result
            
        probability = result["fake_probability"]
        label = "Synthetic" if probability > 0.5 else "Genuine"
        
        prediction = Prediction(
            evidence_id=evidence_id,
            module="voice",
            model_name="Wav2Vec2",
            model_version="1.0",
            dataset_version="ASVspoof Base",
            prediction_label=label,
            confidence=probability if label == "Synthetic" else (1 - probability),
            processing_time_ms=processing_time_ms
        )
        db.add(prediction)
        db.commit()
        
        return {
            "status": "success",
            "fake_probability": probability,
            "spectrograms": result["spectrograms"]
        }
    except Exception as e:
        logger.error(f"Error processing voice task: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Global Email Pipeline
email_pipeline = None

def get_email_pipeline():
    global email_pipeline
    if email_pipeline is None:
        logger.info("Initializing Email ML Pipeline...")
        from ..ml.email.pipeline import EmailPipeline
        email_pipeline = EmailPipeline(device="cpu")
    return email_pipeline

@shared_task(bind=True, name="process_email")
def process_email(self, evidence_id: int, sender_email: str, subject: str, body: str, has_attachments: bool):
    db: Session = SessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"status": "error", "message": "Evidence not found"}

        pipeline = get_email_pipeline()
        
        import time
        start_time = time.time()
        result = pipeline.analyze_email(sender_email, subject, body, has_attachments)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("status") == "error":
            return result
            
        probability = result["final_phishing_probability"]
        label = "Phishing" if probability > 0.5 else "Legitimate"
        
        prediction = Prediction(
            evidence_id=evidence_id,
            module="email",
            model_name="DistilBERT-Phishing",
            model_version="1.0",
            dataset_version="Enron+Phishing",
            prediction_label=label,
            confidence=probability if label == "Phishing" else (1 - probability),
            processing_time_ms=processing_time_ms
        )
        db.add(prediction)
        
        db.commit()
        
        return {
            "status": "success",
            "final_phishing_probability": probability,
            "header_risk_score": result["header_risk_score"],
            "header_flags": result["header_flags"],
            "shap_explanation": result["shap_explanation"]
        }
    except Exception as e:
        logger.error(f"Error processing email task: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Global URL Pipeline
url_pipeline = None

def get_url_pipeline():
    global url_pipeline
    if url_pipeline is None:
        logger.info("Initializing URL ML Pipeline...")
        from ..ml.url.pipeline import URLPipeline
        url_pipeline = URLPipeline()
    return url_pipeline

@shared_task(bind=True, name="process_url")
def process_url(self, evidence_id: int, target_url: str):
    db: Session = SessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"status": "error", "message": "Evidence not found"}

        pipeline = get_url_pipeline()
        
        import time
        start_time = time.time()
        result = pipeline.analyze_url(target_url)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("status") == "error":
            return result
            
        probability = result["malicious_probability"]
        label = "Malicious" if probability > 0.5 else "Benign"
        
        prediction = Prediction(
            evidence_id=evidence_id,
            module="url",
            model_name="RandomForest-Lexical",
            model_version="1.0",
            dataset_version="Simulated-RF",
            prediction_label=label,
            confidence=probability if label == "Malicious" else (1 - probability),
            processing_time_ms=processing_time_ms
        )
        db.add(prediction)
        db.commit()
        
        return {
            "status": "success",
            "malicious_probability": probability,
            "features_extracted": result["features_extracted"]
        }
    except Exception as e:
        logger.error(f"Error processing URL task: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Global Network Pipeline
network_pipeline = None

def get_network_pipeline():
    global network_pipeline
    if network_pipeline is None:
        logger.info("Initializing Network IDS Pipeline...")
        from ..ml.network.pipeline import NetworkPipeline
        network_pipeline = NetworkPipeline()
    return network_pipeline

@shared_task(bind=True, name="process_network_flow")
def process_network_flow(self, evidence_id: int, flow_data: dict):
    db: Session = SessionLocal()
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            return {"status": "error", "message": "Evidence not found"}

        pipeline = get_network_pipeline()
        
        import time
        start_time = time.time()
        result = pipeline.analyze_flow(flow_data)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        if result.get("status") == "error":
            return result
            
        probability = result["anomaly_probability"]
        label = "Anomalous" if probability > 0.5 else "Normal"
        
        prediction = Prediction(
            evidence_id=evidence_id,
            module="network",
            model_name="Autoencoder",
            model_version="1.0",
            dataset_version="Simulated-AE",
            prediction_label=label,
            confidence=probability if label == "Anomalous" else (1 - probability),
            processing_time_ms=processing_time_ms
        )
        db.add(prediction)
        db.commit()
        
        return {
            "status": "success",
            "anomaly_probability": probability,
            "reconstruction_error_mse": result["reconstruction_error_mse"],
            "flow_metrics": result["flow_metrics"]
        }
    except Exception as e:
        logger.error(f"Error processing network task: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Global Fusion Pipeline
fusion_pipeline = None

def get_fusion_pipeline():
    global fusion_pipeline
    if fusion_pipeline is None:
        logger.info("Initializing Risk Fusion Pipeline...")
        from ..ml.fusion.pipeline import RiskFusionPipeline
        fusion_pipeline = RiskFusionPipeline()
    return fusion_pipeline

@shared_task(bind=True, name="process_risk_fusion")
def process_risk_fusion(self, case_id: int):
    """
    Aggregates all predictions for a given case and calculates the holistic risk score.
    """
    db: Session = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return {"status": "error", "message": "Case not found"}

        # Fetch all predictions associated with this case's evidence
        evidence_list = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        evidence_ids = [e.id for e in evidence_list]
        
        predictions = db.query(Prediction).filter(Prediction.evidence_id.in_(evidence_ids)).all()
        
        # Convert to dicts for the pipeline
        pred_dicts = []
        for p in predictions:
            pred_dicts.append({
                "module": p.module,
                "prediction_label": p.prediction_label,
                "confidence": p.confidence
            })

        pipeline = get_fusion_pipeline()
        
        import time
        start_time = time.time()
        result = pipeline.fuse_risks(pred_dicts)
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # In a full system, we might save this Case Risk Score back to the database.
        # For now, we update the Case object (if we had a risk_score column) 
        # or just return it to the frontend via the API.
        
        return {
            "status": "success",
            "case_id": case_id,
            "overall_risk_score": result["overall_risk_score"],
            "threat_level": result["threat_level"],
            "critical_alerts": result["critical_alerts"],
            "modules_analyzed": result["modules_analyzed"],
            "processing_time_ms": processing_time_ms
        }
    except Exception as e:
        logger.error(f"Error processing risk fusion task: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
