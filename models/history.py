from datetime import datetime
import uuid

class HistoryItem:
    def __init__(self, user_email, prompt, code, model='deepseek'):
        self.id = str(uuid.uuid4())[:8]
        self.user_email = user_email
        self.prompt = prompt
        self.code = code
        self.model = model
        self.timestamp = datetime.now().isoformat()
        self.tokens_used = len(code) // 4  # rough estimate
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_email': self.user_email,
            'prompt': self.prompt[:100],
            'code': self.code,
            'model': self.model,
            'timestamp': self.timestamp,
            'tokens_used': self.tokens_used
        }