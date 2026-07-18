from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq import Groq
import os, json, zipfile, tempfile, time
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# ============ API KEY ============
GROQ_KEY = os.environ.get('GROQ_KEY', '')

# ============ STORAGE ============
request_log = defaultdict(list)
history = []

@app.route('/')
def home():
    return jsonify({
        'status': 'alive',
        'api': 'groq',
        'key_set': bool(GROQ_KEY)
    })

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive'})

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    model = data.get('model', 'groq')

    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400

    if not GROQ_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    # Rate limit
    ip = request.remote_addr
    now = time.time()
    request_log[ip] = [t for t in request_log[ip] if now - t < 60]
    if len(request_log[ip]) >= 30:
        return jsonify({'error': 'Rate limit. Wait 1 minute.'}), 429
    request_log[ip].append(now)

    try:
        client = Groq(api_key=GROQ_KEY)
        chat = client.chat.completions.create(
            messages=[
                {'role': 'system', 'content': 'You are a helpful, intelligent AI assistant. Answer naturally and completely.'},
                {'role': 'user', 'content': prompt}
            ],
            model='llama-3.1-70b-versatile',
            temperature=0.8,
            max_tokens=4096
        )
        response = chat.choices[0].message.content

        history.append({
            'prompt': prompt[:200],
            'response': response[:500],
            'time': datetime.now().isoformat()
        })
        if len(history) > 100:
            history.pop(0)

        return jsonify({
            'success': True,
            'response': response,
            'model': 'groq'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/models', methods=['GET'])
def models():
    return jsonify({
        'models': [
            {'id': 'groq', 'name': '⚡ Groq (Llama 3.1 70B)', 'free': True}
        ]
    })

@app.route('/download_zip', methods=['POST'])
def download_zip():
    files = request.json.get('files', {})
    if not files:
        return jsonify({'error': 'No files'}), 400

    tmp = tempfile.mkdtemp()
    zp = os.path.join(tmp, f"code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")

    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            zf.write(path, name)

    return send_file(zp, as_attachment=True, download_name='code.zip')

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify({'history': history[-20:]})

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        'total_requests': len(history),
        'uptime': 'running'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
