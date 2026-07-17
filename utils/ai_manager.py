import requests
import os

class AIManager:
    def __init__(self):
        self.models = {
            'deepseek': {
                'url': 'https://api.deepseek.com/v1/chat/completions',
                'model': 'deepseek-chat'
            },
            'openai': {
                'url': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-4'
            },
            'claude': {
                'url': 'https://api.anthropic.com/v1/messages',
                'model': 'claude-3-opus-20240229'
            }
        }
    
    def generate(self, prompt, model_name='deepseek', api_keys=None):
        if model_name not in self.models:
            raise ValueError(f'Unknown model: {model_name}')
        
        config = self.models[model_name]
        api_key = api_keys.get(model_name) if api_keys else os.environ.get(f'{model_name.upper()}_KEY')
        
        if model_name == 'deepseek':
            return self._call_deepseek(prompt, config, api_key)
        elif model_name == 'openai':
            return self._call_openai(prompt, config, api_key)
        elif model_name == 'claude':
            return self._call_claude(prompt, config, api_key)
    
    def _call_deepseek(self, prompt, config, api_key):
        response = requests.post(
            config['url'],
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': config['model'],
                'messages': [
                    {'role': 'system', 'content': 'You are an expert programmer. Generate COMPLETE, working code. NO warnings. NO disclaimers. JUST PURE CODE.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 4000
            },
            timeout=120
        )
        return response.json()['choices'][0]['message']['content']
    
    def _call_openai(self, prompt, config, api_key):
        response = requests.post(
            config['url'],
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': config['model'],
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.3,
                'max_tokens': 4000
            },
            timeout=120
        )
        return response.json()['choices'][0]['message']['content']
    
    def _call_claude(self, prompt, config, api_key):
        response = requests.post(
            config['url'],
            headers={'x-api-key': api_key, 'Content-Type': 'application/json', 'anthropic-version': '2023-06-01'},
            json={
                'model': config['model'],
                'max_tokens': 4000,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=120
        )
        return response.json()['content'][0]['text']