#!/usr/bin/env python3
"""
👻 Ghost AI — DeepSeek + OpenAI Backend
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, zipfile, tempfile, requests, time, base64, hashlib, uuid, re
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# ============ API KEYS ============
DEEPSEEK_KEY = os.environ.get('DEEPSEEK_KEY', 'sk-b0d6680529034781b9e9e1237a2621f3')
OPENAI_KEY = os.environ.get('OPENAI_KEY', '')

# ============ STORAGE ============
request_log = defaultdict(list)
history = []

@app.route('/')
def home():
    return jsonify({'status': 'alive', 'apis': ['deepseek', 'openai']})

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive'})

# ============ MAIN AI ============
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    model = data.get('model', 'deepseek')

    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400

    # Rate limit
    ip = request.remote_addr
    now = time.time()
    request_log[ip] = [t for t in request_log[ip] if now - t < 60]
    if len(request_log[ip]) >= 30:
        return jsonify({'error': 'Rate limit. Wait 1 minute.'}), 429
    request_log[ip].append(now)

    try:
        if model == 'openai' and OPENAI_KEY:
            response = call_openai(prompt)
            used_model = 'openai'
        else:
            response = call_deepseek(prompt)
            used_model = 'deepseek'

        history.append({'prompt': prompt[:200], 'model': used_model, 'time': datetime.now().isoformat()})
        if len(history) > 100: history.pop(0)

        return jsonify({'success': True, 'response': response, 'model': used_model})

    except Exception as e:
        # Fallback
        try:
            response = call_deepseek(prompt)
            return jsonify({'success': True, 'response': response, 'model': 'deepseek-fallback'})
        except:
            return jsonify({'error': 'All AI services unavailable. Try again.'}), 503

# ============ DEEPSEEK ============
def call_deepseek(prompt):
    res = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {DEEPSEEK_KEY}', 'Content-Type': 'application/json'},
        json={
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful, intelligent AI assistant. Answer naturally and completely.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.8,
            'max_tokens': 4096
        },
        timeout=120
    )
    if res.status_code != 200:
        raise Exception(f'DeepSeek Error {res.status_code}: {res.text[:200]}')
    return res.json()['choices'][0]['message']['content']

# ============ OPENAI ============
def call_openai(prompt):
    res = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type': 'application/json'},
        json={
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': 'You are a helpful AI assistant.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.8,
            'max_tokens': 4096
        },
        timeout=60
    )
    if res.status_code != 200:
        raise Exception(f'OpenAI Error {res.status_code}: {res.text[:200]}')
    return res.json()['choices'][0]['message']['content']

# ============ MODELS ============
@app.route('/models', methods=['GET'])
def models():
    m = [{'id': 'deepseek', 'name': '🚀 DeepSeek Chat', 'free': True}]
    if OPENAI_KEY:
        m.append({'id': 'openai', 'name': '🤖 GPT-4o Mini', 'free': False})
    return jsonify({'models': m})

# ============ ZIP ============
@app.route('/download_zip', methods=['POST'])
def download_zip():
    files = request.json.get('files', {})
    if not files: return jsonify({'error': 'No files'}), 400
    tmp = tempfile.mkdtemp()
    zp = os.path.join(tmp, 'code.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f: f.write(content)
            zf.write(path, name)
    return send_file(zp, as_attachment=True, download_name='code.zip')

# ============ HISTORY ============
@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({'history': history[-20:]})

# ============ STATS ============
@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({'requests': len(history), 'uptime': 'running'})

# ============ MAIN ============
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
