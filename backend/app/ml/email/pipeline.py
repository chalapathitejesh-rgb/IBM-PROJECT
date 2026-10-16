from .rules import EmailHeaderAnalyzer
from .model import PhishingEmailDetector

class EmailPipeline:
    """Fuses rule-based header analysis with deep learning text classification."""
    def __init__(self, device='cpu'):
        self.header_analyzer = EmailHeaderAnalyzer()
        self.text_detector = PhishingEmailDetector(device=device)
        
    def analyze_email(self, sender_email: str, subject: str, body: str, has_attachments: bool):
        # 1. Rule-based analysis
        header_results = self.header_analyzer.analyze_headers(sender_email, subject, has_attachments)
        
        # 2. Deep Learning Text Analysis
        text_phishing_prob = self.text_detector.predict(body)
        
        # 3. Generate XAI Explanation (SHAP)
        shap_explanation = self.text_detector.generate_shap_explanation(body)
        
        # 4. Hybrid Fusion (Weighted average: 40% Headers, 60% Body)
        rule_score = header_results["rule_risk_score"]
        final_risk_score = (rule_score * 0.4) + (text_phishing_prob * 0.6)
        
        return {
            "final_phishing_probability": final_risk_score,
            "text_model_probability": text_phishing_prob,
            "header_risk_score": rule_score,
            "header_flags": header_results["flags"],
            "shap_explanation": shap_explanation,
            "status": "success"
        }
