from .features import URLFeatureExtractor
from .model import MaliciousURLDetector

class URLPipeline:
    def __init__(self):
        self.extractor = URLFeatureExtractor()
        self.detector = MaliciousURLDetector()
        
    def analyze_url(self, url: str):
        # 1. Extract lexical features
        features = self.extractor.extract_features(url)
        
        # 2. Run Random Forest ML inference
        malicious_prob = self.detector.predict_proba(features)
        
        # 3. Generate Explainability (Feature Importance mapping)
        # We map the extracted values back to their names to show the user WHY it was flagged
        feature_names = [
            "URL Length", "Hostname Length", "Num Dots", "Num Hyphens", 
            "Contains @", "Heavy Subdomains", "Suspicious TLD", "Is Bare IP", "Has HTTPS", 
            "Brand Spoof Words", "Entropy Score"
        ]
        
        explanation = [
            {"feature": name, "value": val} 
            for name, val in zip(feature_names, features)
        ]
        
        return {
            "malicious_probability": malicious_prob,
            "features_extracted": explanation,
            "status": "success"
        }
