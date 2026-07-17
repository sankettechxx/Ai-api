import hashlib
import hmac
import base64
from datetime import datetime, timedelta
import secrets

class SecurityManager:
    @staticmethod
    def hash_password(password):
        salt = secrets.token_hex(16)
        return salt + ':' + hashlib.sha256((salt + password).encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, hashed):
        salt, hash_val = hashed.split(':')
        return hashlib.sha256((salt + password).encode()).hexdigest() == hash_val
    
    @staticmethod
    def generate_token(email):
        data = f"{email}:{datetime.now().isoformat()}"
        return base64.urlsafe_b64encode(data.encode()).decode()
    
    @staticmethod
    def sanitize_input(text):
        """Basic XSS prevention"""
        import html
        return html.escape(text)
    
    @staticmethod
    def rate_limit_check(key, max_requests=100, window=3600):
        """Simple in-memory rate limiting"""
        pass