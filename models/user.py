from datetime import datetime

class User:
    def __init__(self, email, name=None, plan='free'):
        self.email = email
        self.name = name or email.split('@')[0]
        self.plan = plan
        self.created_at = datetime.now().isoformat()
        self.api_keys = {}
        self.generations = 0
        self.last_login = None
    
    def to_dict(self):
        return {
            'email': self.email,
            'name': self.name,
            'plan': self.plan,
            'created_at': self.created_at,
            'generations': self.generations,
            'last_login': self.last_login
        }
    
    def can_generate(self):
        limits = {'free': 100, 'pro': 99999, 'enterprise': 999999}
        return self.generations < limits.get(self.plan, 100)