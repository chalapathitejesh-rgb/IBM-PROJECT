import math
import re
from urllib.parse import urlparse

class URLFeatureExtractor:
    """Extracts lexical and structural features from a URL to detect PhishTank-style threats."""
    
    def __init__(self):
        # Expanded suspicious keywords common in PhishTank URLs
        self.suspicious_words = [
            'login', 'secure', 'account', 'update', 'banking', 'verify', 
            'webscr', 'ebayisapi', 'paypal', 'admin', 'service', 'confirm',
            'support', 'appleid', 'microsoft', 'recover', 'wallet'
        ]
        # High-risk Top Level Domains often used by phishers
        self.high_risk_tlds = ['.xyz', '.top', '.club', '.online', '.site', '.tk', '.ml', '.ga', '.cf', '.gq']
        
    def _entropy(self, string):
        """Calculates Shannon entropy of the string."""
        if not string: return 0
        prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
        entropy = - sum([p * math.log(p) / math.log(2.0) for p in prob])
        return entropy

    def extract_features(self, url: str) -> list:
        # Ensure scheme is present for parsing
        if not url.startswith('http'):
            url = 'http://' + url
            
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        path = parsed.path or ""
        
        # 1. Length features
        url_length = len(url)
        hostname_length = len(hostname)
        
        # 2. Character counts & Structural
        num_dots = hostname.count('.')
        num_hyphens = hostname.count('-')
        num_at = url.count('@') # Very malicious indicator
        num_queries = url.count('?')
        
        # 3. PhishTank specific structural traits
        # Check if hostname is literally an IP address
        has_ip = 1 if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', hostname) else 0
        has_https = 1 if parsed.scheme == 'https' else 0
        
        # Look for multiple subdomains (e.g., paypal.secure.login.com.xyz)
        is_subdomain_heavy = 1 if num_dots > 2 else 0
        
        # Look for high risk TLDs
        has_suspicious_tld = 1 if any(hostname.endswith(tld) for tld in self.high_risk_tlds) else 0
        
        # 4. Keyword presence (Brand Spoofing)
        url_lower = url.lower()
        suspicious_word_count = sum(1 for word in self.suspicious_words if word in url_lower)
        
        # 5. Entropy (Phishing URLs often have high entropy due to random base64 tokens in path)
        url_entropy = self._entropy(url)
        path_entropy = self._entropy(path)
        
        return [
            url_length, 
            hostname_length, 
            num_dots, 
            num_hyphens, 
            num_at, 
            is_subdomain_heavy,
            has_suspicious_tld, 
            has_ip, 
            has_https, 
            suspicious_word_count, 
            max(url_entropy, path_entropy)
        ]
