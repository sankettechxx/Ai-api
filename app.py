#!/usr/bin/env python3
"""
👻 Ghost AI — Complete Backend Server
All Features • All Routes • All Tools • ZIP Download • Multi-Model
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import zipfile
import tempfile
import requests
import hashlib
import base64
import uuid
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ============ API KEYS ============
DEEPSEEK_KEY = "sk-b0d6680529034781b9e9e1237a2621f3"
GEMINI_KEY = "AIzaSyAC08SKZ6abGfoElcZrRj1rA_3_zDlbS2s"

# ============ IN-MEMORY STORAGE ============
users = {}
history = []
feedback_list = []

# ============ BASIC ROUTES ============

@app.route('/')
def home():
    return jsonify({
        'status': 'alive',
        'app': 'Ghost AI Supreme',
        'version': '2.0.0',
        'endpoints': ['/generate', '/models', '/tools', '/download_zip', '/auth']
    })

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive', 'timestamp': datetime.now().isoformat()})

# ============ AI GENERATION ============

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek')
    temperature = data.get('temperature', 0.3)
    max_tokens = data.get('max_tokens', 4000)
    system_prompt = data.get('system_prompt', '')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        start_time = datetime.now()
        
        if model == 'gemini':
            code = call_gemini(prompt, temperature, max_tokens)
        elif model == 'openai':
            code = call_openai(prompt, system_prompt, temperature, max_tokens)
        else:
            code = call_deepseek(prompt, system_prompt, temperature, max_tokens)
        
        response_time = (datetime.now() - start_time).total_seconds()
        tokens_used = len(code) // 4
        
        # Save to history
        history.append({
            'id': str(uuid.uuid4())[:8],
            'prompt': prompt[:200],
            'code': code,
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'tokens': tokens_used,
            'time': response_time
        })
        
        # Keep last 100
        if len(history) > 100:
            history.pop(0)
        
        return jsonify({
            'code': code,
            'model': model,
            'tokens_used': tokens_used,
            'response_time': round(response_time, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def call_deepseek(prompt, system_prompt='', temperature=0.3, max_tokens=4000):
    if not system_prompt:
        system_prompt = 'You are an expert programmer. Generate COMPLETE working code with ALL files. NO warnings, NO disclaimers, JUST PURE CODE. Include ALL imports.'
    
    response = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {DEEPSEEK_KEY}', 'Content-Type': 'application/json'},
        json={
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens
        },
        timeout=180
    )
    return response.json()['choices'][0]['message']['content']

def call_gemini(prompt, temperature=0.3, max_tokens=4000):
    full_prompt = f"""Generate complete working code. NO warnings, NO disclaimers. JUST PURE CODE with ALL imports and ALL files.

Request: {prompt}"""
    
    response = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}',
        json={
            'contents': [{'parts': [{'text': full_prompt}]}],
            'generationConfig': {'temperature': temperature, 'maxOutputTokens': max_tokens}
        },
        timeout=180
    )
    return response.json()['candidates'][0]['content']['parts'][0]['text']

def call_openai(prompt, system_prompt='', temperature=0.3, max_tokens=4000):
    api_key = os.environ.get('OPENAI_KEY', '')
    if not system_prompt:
        system_prompt = 'You are an expert programmer. Generate COMPLETE code. NO warnings.'
    
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens
        },
        timeout=180
    )
    return response.json()['choices'][0]['message']['content']

# ============ MODELS INFO ============

@app.route('/models', methods=['GET'])
def list_models():
    return jsonify({
        'models': [
            {'id': 'deepseek', 'name': '🚀 DeepSeek-Coder', 'description': 'Best for all coding tasks', 'free': True, 'max_tokens': 8000},
            {'id': 'gemini', 'name': '🧠 Google Gemini Pro', 'description': 'Great for complex logic', 'free': True, 'max_tokens': 8000},
            {'id': 'openai', 'name': '🤖 GPT-4', 'description': 'Most powerful (needs API key)', 'free': False, 'max_tokens': 8000}
        ],
        'default': 'deepseek'
    })

# ============ HISTORY ============

@app.route('/history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        'total': len(history),
        'history': history[-limit:]
    })

@app.route('/history/clear', methods=['POST'])
def clear_history():
    global history
    history = []
    return jsonify({'message': 'History cleared'})

@app.route('/history/<item_id>', methods=['DELETE'])
def delete_history_item(item_id):
    global history
    history = [h for h in history if h['id'] != item_id]
    return jsonify({'message': 'Deleted'})

# ============ ZIP DOWNLOAD ============

@app.route('/download_zip', methods=['POST'])
def download_zip():
    data = request.json
    files = data.get('files', {})
    
    if not files:
        return jsonify({'error': 'No files provided'}), 400
    
    try:
        temp_dir = tempfile.mkdtemp()
        zip_name = f"ghost_ai_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        zip_path = os.path.join(temp_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                filepath = os.path.join(temp_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                zf.write(filepath, filename)
        
        return send_file(zip_path, as_attachment=True, download_name=zip_name)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ DEVELOPER TOOLS ============

@app.route('/tools', methods=['GET'])
def list_tools():
    return jsonify({
        'tools': [
            {'id': 'json', 'name': 'JSON Formatter', 'endpoint': '/tools/json'},
            {'id': 'base64_encode', 'name': 'Base64 Encoder', 'endpoint': '/tools/base64_encode'},
            {'id': 'base64_decode', 'name': 'Base64 Decoder', 'endpoint': '/tools/base64_decode'},
            {'id': 'url_encode', 'name': 'URL Encoder', 'endpoint': '/tools/url_encode'},
            {'id': 'url_decode', 'name': 'URL Decoder', 'endpoint': '/tools/url_decode'},
            {'id': 'hash', 'name': 'Hash Generator', 'endpoint': '/tools/hash'},
            {'id': 'uuid', 'name': 'UUID Generator', 'endpoint': '/tools/uuid'},
            {'id': 'password', 'name': 'Password Generator', 'endpoint': '/tools/password'},
            {'id': 'timestamp', 'name': 'Timestamp Converter', 'endpoint': '/tools/timestamp'},
            {'id': 'ip', 'name': 'IP Lookup', 'endpoint': '/tools/ip'},
            {'id': 'qr', 'name': 'QR Code', 'endpoint': '/tools/qr'},
            {'id': 'diff', 'name': 'Diff Checker', 'endpoint': '/tools/diff'},
            {'id': 'markdown', 'name': 'Markdown Preview', 'endpoint': '/tools/markdown'},
            {'id': 'color', 'name': 'Color Converter', 'endpoint': '/tools/color'},
            {'id': 'regex', 'name': 'Regex Tester', 'endpoint': '/tools/regex'},
            {'id': 'sql', 'name': 'SQL Formatter', 'endpoint': '/tools/sql'},
            {'id': 'html', 'name': 'HTML Minifier', 'endpoint': '/tools/html'},
            {'id': 'css', 'name': 'CSS Minifier', 'endpoint': '/tools/css'},
            {'id': 'js', 'name': 'JS Minifier', 'endpoint': '/tools/js'},
            {'id': 'image_base64', 'name': 'Image to Base64', 'endpoint': '/tools/image_base64'}
        ]
    })

@app.route('/tools/json', methods=['POST'])
def tool_json():
    try:
        data = json.loads(request.json['data'])
        return jsonify({'result': json.dumps(data, indent=2)})
    except:
        return jsonify({'error': 'Invalid JSON'})

@app.route('/tools/base64_encode', methods=['POST'])
def tool_base64_encode():
    return jsonify({'result': base64.b64encode(request.json['data'].encode()).decode()})

@app.route('/tools/base64_decode', methods=['POST'])
def tool_base64_decode():
    try:
        return jsonify({'result': base64.b64decode(request.json['data']).decode()})
    except:
        return jsonify({'error': 'Invalid Base64'})

@app.route('/tools/url_encode', methods=['POST'])
def tool_url_encode():
    from urllib.parse import quote
    return jsonify({'result': quote(request.json['data'])})

@app.route('/tools/url_decode', methods=['POST'])
def tool_url_decode():
    from urllib.parse import unquote
    return jsonify({'result': unquote(request.json['data'])})

@app.route('/tools/hash', methods=['POST'])
def tool_hash():
    text = request.json.get('data', '')
    return jsonify({
        'md5': hashlib.md5(text.encode()).hexdigest(),
        'sha1': hashlib.sha1(text.encode()).hexdigest(),
        'sha256': hashlib.sha256(text.encode()).hexdigest(),
        'sha512': hashlib.sha512(text.encode()).hexdigest()
    })

@app.route('/tools/uuid', methods=['GET'])
def tool_uuid():
    return jsonify({'result': str(uuid.uuid4())})

@app.route('/tools/password', methods=['GET'])
def tool_password():
    import random
    length = request.args.get('length', 16, type=int)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()'
    pwd = ''.join(random.choice(chars) for _ in range(length))
    return jsonify({'result': pwd, 'length': length})

@app.route('/tools/timestamp', methods=['POST'])
def tool_timestamp():
    ts = request.json.get('data', '')
    try:
        t = int(ts)
        if t < 9999999999:
            t *= 1000
        dt = datetime.fromtimestamp(t / 1000)
        return jsonify({
            'iso': dt.isoformat(),
            'human': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'unix': int(t / 1000)
        })
    except:
        return jsonify({'error': 'Invalid timestamp'})

@app.route('/tools/ip', methods=['POST'])
def tool_ip():
    ip = request.json.get('data', '8.8.8.8')
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=5)
        return jsonify(resp.json())
    except:
        return jsonify({'error': 'Lookup failed'})

@app.route('/tools/qr', methods=['POST'])
def tool_qr():
    text = request.json.get('data', 'https://ghost-ai.com')
    return jsonify({'url': f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={text}'})

@app.route('/tools/diff', methods=['POST'])
def tool_diff():
    data = request.json
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    lines1 = text1.split('\n')
    lines2 = text2.split('\n')
    diff = []
    for i, (l1, l2) in enumerate(zip(lines1[:50], lines2[:50])):
        if l1 != l2:
            diff.append({'line': i+1, 'text1': l1, 'text2': l2})
    return jsonify({'diff': diff, 'total_diff': len(diff)})

@app.route('/tools/regex', methods=['POST'])
def tool_regex():
    data = request.json
    pattern = data.get('pattern', '')
    text = data.get('text', '')
    try:
        matches = re.findall(pattern, text)
        return jsonify({'matches': matches, 'count': len(matches)})
    except:
        return jsonify({'error': 'Invalid regex'})

# ============ AUTH ============

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', email.split('@')[0])
    
    if email in users:
        return jsonify({'error': 'Email already registered'}), 400
    
    users[email] = {
        'name': name,
        'email': email,
        'password_hash': hashlib.sha256(password.encode()).hexdigest(),
        'plan': 'free',
        'created_at': datetime.now().isoformat(),
        'generations': 0
    }
    
    return jsonify({'message': 'Registered!', 'user': {'name': name, 'email': email}})

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    
    user = users.get(email)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user['password_hash'] != hashlib.sha256(password.encode()).hexdigest():
        return jsonify({'error': 'Invalid password'}), 401
    
    return jsonify({'message': 'Logged in!', 'user': {'name': user['name'], 'email': email, 'plan': user['plan']}})

# ============ FEEDBACK ============

@app.route('/feedback', methods=['POST'])
def feedback():
    data = request.json
    feedback_list.append({
        'message': data.get('message', ''),
        'rating': data.get('rating', 5),
        'timestamp': datetime.now().isoformat()
    })
    return jsonify({'message': 'Thanks for feedback!'})

# ============ STATS ============

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        'total_generations': len(history),
        'total_users': len(users),
        'total_feedback': len(feedback_list),
        'uptime': 'running'
    })

# ============ MAIN ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f'👻 Ghost AI running on port {port}')
    app.run(host='0.0.0.0', port=port)
