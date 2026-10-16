import re
from email_validator import validate_email, EmailNotValidError

class EmailHeaderAnalyzer:
    """Analyzes email headers and metadata for common phishing indicators."""
    
    def __init__(self):
        # Known suspicious keywords often found in phishing subjects
        self.suspicious_subject_keywords = [
            "urgent", "action required", "account suspended", 
            "invoice", "password reset", "verify", "winner"
        ]

    def analyze_headers(self, sender_email: str, subject: str, has_attachments: bool):
        score = 0
        reasons = []

        # 1. Validate Sender Email Format & Domain
        try:
            valid = validate_email(sender_email)
            domain = valid.domain
            
            # Simple heuristic for freemail domains often used in targeted phishing
            freemail_domains = ["gmail.com", "yahoo.com", "hotmail.com", "aol.com"]
            if domain in freemail_domains:
                score += 0.2
                reasons.append("Sender uses a free email provider.")
        except EmailNotValidError as e:
            score += 0.8
            reasons.append(f"Invalid sender email format: {str(e)}")

        # 2. Analyze Subject Line
        subject_lower = subject.lower()
        keyword_hits = [kw for kw in self.suspicious_subject_keywords if kw in subject_lower]
        if keyword_hits:
            score += 0.3
            reasons.append(f"Suspicious subject keywords found: {', '.join(keyword_hits)}.")
            
        # 3. Attachments
        if has_attachments:
            score += 0.2
            reasons.append("Email contains attachments (potential malware payload).")
            
        # Cap score at 1.0
        return {
            "rule_risk_score": min(score, 1.0),
            "flags": reasons
        }
