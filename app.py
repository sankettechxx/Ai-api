from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, zipfile, tempfile, requests, time
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

GROQ_KEY = os.environ.get('GROQ_KEY', '')

request_log = defaultdict(list)

@app.route('/')
def home():
    return jsonify({'status': 'alive', 'api': 'groq', 'key_set': bool(GROQ_KEY)})

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive'})

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    
    if not GROQ_KEY:
        return jsonify({'error': 'API key not configured'}), 500
    
    try:
        # Updated models (July 2026)
        # Recommended: llama-3.3-70b-versatile (strong) or llama-3.1-8b-instant (fast/cheap)
        res = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'llama-3.3-70b-versatile',   # ← Changed here
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful, intelligent AI assistant. Answer naturally and completely.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.8,
                'max_tokens': 4096
            },
            timeout=90
        )
        
        if res.status_code != 200:
            return jsonify({'error': f'Groq Error {res.status_code}: {res.text[:400]}'}), 500
        
        response = res.json()['choices'][0]['message']['content']
        return jsonify({
            'success': True, 
            'response': response, 
            'model': 'llama-3.3-70b-versatile'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_zip', methods=['POST'])
def download_zip():
    files = request.json.get('files', {})
    if not files: 
        return jsonify({'error': 'No files'}), 400
    
    tmp = tempfile.mkdtemp()
    zp = os.path.join(tmp, 'code.zip')
    
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            zf.write(path, name)
    
    return send_file(zp, as_attachment=True, download_name='code.zip')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
