class RiskFusionPipeline:
    def __init__(self):
        # Weights for each module type
        # These reflect the relative severity of different attack vectors
        self.module_weights = {
            "network": 0.35, # Network intrusion is highly critical
            "deepfake": 0.20,
            "voice": 0.15,
            "url": 0.15,
            "email": 0.15
        }

    def fuse_risks(self, predictions: list) -> dict:
        """
        Fuses predictions from multiple models into a single holistic threat score.
        predictions: List of SQLAlchemy Prediction objects (converted to dicts)
        """
        if not predictions:
            return {"overall_risk_score": 0.0, "threat_level": "Safe"}

        total_weight_applied = 0.0
        weighted_sum = 0.0
        
        # Track highest severity threat for explainability
        critical_alerts = []

        for pred in predictions:
            module = pred.get("module")
            # If a label indicates malicious behavior, use the confidence.
            # If it's safe/benign, the risk contribution is 0 or low.
            is_malicious = pred.get("prediction_label") in ["Fake", "Phishing", "Malicious", "Anomalous"]
            
            # Base risk is the confidence of the malicious prediction
            raw_risk = float(pred.get("confidence", 0.0)) if is_malicious else (1.0 - float(pred.get("confidence", 0.0)))
            
            weight = self.module_weights.get(module, 0.1)
            
            weighted_sum += (raw_risk * weight)
            total_weight_applied += weight
            
            if raw_risk > 0.75:
                critical_alerts.append(f"High-risk indicator found in {module} ({pred.get('prediction_label')} - {int(raw_risk*100)}% confidence)")

        # Normalize score to 0-100 range
        if total_weight_applied == 0:
            final_score = 0.0
        else:
            final_score = (weighted_sum / total_weight_applied) * 100.0

        # Determine Threat Level Category
        if final_score > 75.0:
            threat_level = "Critical"
        elif final_score > 50.0:
            threat_level = "High"
        elif final_score > 25.0:
            threat_level = "Medium"
        else:
            threat_level = "Low"

        return {
            "overall_risk_score": round(final_score, 2),
            "threat_level": threat_level,
            "critical_alerts": critical_alerts,
            "modules_analyzed": len(predictions)
        }
