from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, zipfile, tempfile, requests, time, base64, hashlib, uuid
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# ============ API KEY ============
GEMINI_KEY = "AIzaSyAd9JIitUC03XJkrfqpkUDqTUHLUh3Ak1E"

# ============ STORAGE ============
request_log = defaultdict(list)
history = []

@app.route('/')
def home():
    return jsonify({'status': 'alive', 'api': 'gemini'})

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive'})

# ============ MAIN AI ============
@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    
    # Rate limit
    ip = request.remote_addr
    now = time.time()
    request_log[ip] = [t for t in request_log[ip] if now - t < 60]
    if len(request_log[ip]) >= 60:
        return jsonify({'error': 'Rate limit. Wait 1 minute.'}), 429
    request_log[ip].append(now)
    
    try:
        response = call_gemini(prompt)
        
        history.append({
            'prompt': prompt[:200],
            'response': response[:500],
            'time': datetime.now().isoformat()
        })
        if len(history) > 100:
            history.pop(0)
        
        return jsonify({'success': True, 'response': response, 'model': 'gemini'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def call_gemini(prompt):
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}'
    
    res = requests.post(
        url,
        json={
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': 0.8,
                'maxOutputTokens': 4096
            }
        },
        timeout=60
    )
    
    if res.status_code != 200:
        raise Exception(f'Gemini Error {res.status_code}: {res.text[:200]}')
    
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# ============ MODELS ============
@app.route('/models', methods=['GET'])
def models():
    return jsonify({
        'models': [
            {'id': 'gemini', 'name': '🧠 Gemini 2.0 Flash', 'free': True}
        ]
    })

# ============ ZIP DOWNLOAD ============
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

# ============ HISTORY ============
@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({'history': history[-20:]})

# ============ STATS ============
@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        'total_requests': len(history),
        'uptime': 'running'
    })

# ============ MAIN ============
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
