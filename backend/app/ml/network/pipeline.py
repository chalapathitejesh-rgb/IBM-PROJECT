from .features import NetworkFeatureExtractor
from .model import IDSDetector

class NetworkPipeline:
    def __init__(self):
        self.extractor = NetworkFeatureExtractor()
        self.detector = IDSDetector()
        
    def analyze_flow(self, flow_data: dict):
        # 1. Extract numerical features
        features = self.extractor.extract_features(flow_data)
        
        # 2. Run through Autoencoder
        anomaly_prob, mse = self.detector.detect_anomaly(features)
        
        # 3. Explainability (Feature tracking)
        feature_names = [
            "Duration", "Src Bytes", "Dst Bytes", "Missed Bytes", 
            "Src Packets", "Dst Packets", "Protocol Code"
        ]
        explanation = [
            {"feature": name, "value": val} 
            for name, val in zip(feature_names, features)
        ]
        
        return {
            "anomaly_probability": anomaly_prob,
            "reconstruction_error_mse": mse,
            "flow_metrics": explanation,
            "status": "success"
        }
