import os
import pickle
import numpy as np

class MaliciousURLDetector:
    def __init__(self):
        self.model = None
        model_path = os.path.join(os.path.dirname(__file__), "url_model.pkl")
        if os.path.exists(model_path):
            try:
                with open(model_path, "rb") as f:
                    self.model = pickle.load(f)
            except Exception as e:
                print(f"Warning: Could not load url_model.pkl: {e}")
        
    def predict_proba(self, features: list) -> float:
        """
        Uses trained Random Forest if available, otherwise falls back to heuristic engine.
        """
        if self.model is not None:
            try:
                features_arr = np.array(features).reshape(1, -1)
                # Random Forest predict_proba returns [[prob_benign, prob_malicious]]
                proba = self.model.predict_proba(features_arr)[0][1]
                return float(proba)
            except Exception as e:
                print(f"Error predicting with RF model: {e}")
                
        # Unpack features for heuristic fallback
        url_len, host_len, dots, hyphens, at, is_subdomain_heavy, has_suspicious_tld, has_ip, has_https, susp_words, entropy = features
        
        score = 0.0
        
        # 1. Critical PhishTank Indicators (High Weight)
        if has_ip: 
            score += 0.85 # Bare IPs are almost always malicious in standard traffic
            
        if at > 0: 
            score += 0.75 # Use of '@' in URL to obscure destination
            
        if has_suspicious_tld:
            score += 0.40 # Shady TLDs (.xyz, .tk, .top)
            
        # 2. Structural & Brand Spoofing (Medium Weight)
        if is_subdomain_heavy:
            score += 0.35 # E.g. login.paypal.com.secure.xyz
            
        if susp_words > 0:
            # Phishers stack words like "secure", "verify", "login"
            score += (susp_words * 0.25)
            
        if hyphens > 2:
            score += 0.20 # Typosquatting (e.g. secure-paypal-login.com)
            
        # 3. Security & Obfuscation (Low Weight)
        if not has_https: 
            score += 0.15 # Many PhishTank sites don't bother with SSL (though this is changing)
            
        if entropy > 4.5: 
            score += 0.25 # High entropy usually means random tokens/base64 in the URL path
            
        if url_len > 80: 
            score += 0.15 # Phishing URLs tend to be extremely long to hide the true domain on mobile
            
        # Add a baseline bias correction
        # If it has multiple moderate indicators, it scales quickly
        if score > 0.0:
            score += 0.10
            
        # Cap at 0.99
        prob = min(score, 0.99)
        return prob
