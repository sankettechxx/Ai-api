#!/usr/bin/env python3
"""
👻 Ghost AI — Production-Ready Backend
Multi-API • Rate Limited • Auto-Fallback • Logging
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from groq import Groq
from collections import defaultdict
import os, json, zipfile, tempfile, requests, hashlib, base64, uuid, re, time, logging
from datetime import datetime
from urllib.parse import quote, unquote

# ============ SETUP ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============ API KEYS ============
DEEPSEEK_KEY = "sk-b0d6680529034781b9e9e1237a2621f3"
GEMINI_KEY = "AIzaSyAC08SKZ6abGfoElcZrRj1rA_3_zDlbS2s"
GROQ_KEY = os.environ.get('GROQ_KEY', '')

# ============ RATE LIMITING ============
request_log = defaultdict(list)
RATE_LIMIT = 30  # requests per minute

# ============ STORAGE ============
users = {}
history = []

# ============ BASIC ROUTES ============

@app.route('/')
def home():
    return jsonify({'status': 'alive', 'app': 'Ghost AI', 'apis': ['groq', 'deepseek', 'gemini']})

@app.route('/ping')
def ping():
    return jsonify({'status': 'alive', 'timestamp': datetime.now().isoformat()})

# ============ MAIN AI — RATE LIMITED + FALLBACK ============

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    model = data.get('model', 'groq')
    system_prompt = data.get('system_prompt', '')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    # Rate limit check
    ip = request.remote_addr
    now = time.time()
    request_log[ip] = [t for t in request_log[ip] if now - t < 60]
    if len(request_log[ip]) >= RATE_LIMIT:
        logger.warning(f'Rate limit exceeded for {ip}')
        return jsonify({'error': 'Too many requests. Please wait 1 minute.'}), 429
    request_log[ip].append(now)
    
    logger.info(f'Generate request: model={model}, prompt_len={len(prompt)}')
    
    try:
        start = datetime.now()
        
        # Primary API
        if model == 'gemini':
            response = call_gemini(prompt, system_prompt)
        elif model == 'deepseek':
            response = call_deepseek(prompt, system_prompt)
        else:
            response = call_groq(prompt, system_prompt)
        
        elapsed = (datetime.now() - start).total_seconds()
        
        # Save history
        history.append({
            'id': str(uuid.uuid4())[:8],
            'prompt': prompt[:200],
            'response': response[:500],
            'model': model,
            'timestamp': datetime.now().isoformat(),
            'time': elapsed
        })
        if len(history) > 100:
            history.pop(0)
        
        return jsonify({
            'success': True,
            'response': response,
            'model': model,
            'time_taken': round(elapsed, 2),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f'Primary API ({model}) failed: {str(e)}')
        
        # Fallback 1: DeepSeek
        try:
            logger.info('Trying DeepSeek fallback...')
            response = call_deepseek(prompt)
            return jsonify({
                'success': True,
                'response': response,
                'model': 'deepseek-fallback',
                'fallback': True
            })
        except Exception as e2:
            logger.error(f'DeepSeek fallback failed: {str(e2)}')
            
            # Fallback 2: Gemini
            try:
                logger.info('Trying Gemini fallback...')
                response = call_gemini(prompt)
                return jsonify({
                    'success': True,
                    'response': response,
                    'model': 'gemini-fallback',
                    'fallback': True
                })
            except Exception as e3:
                logger.error(f'All APIs failed: {str(e3)}')
                return jsonify({'error': 'All AI services are currently unavailable. Please try again later.'}), 503

# ============ API CALLS ============

def call_groq(prompt, system_prompt=''):
    if not GROQ_KEY:
        raise Exception('Groq API key not configured')
    
    client = Groq(api_key=GROQ_KEY)
    
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    else:
        messages.append({'role': 'system', 'content': 'You are a helpful, intelligent, and friendly AI assistant. Answer questions naturally in detail. If asked for code, provide complete working code.'})
    messages.append({'role': 'user', 'content': prompt})
    
    chat = client.chat.completions.create(
        messages=messages,
        model='llama-3.1-70b-versatile',
        temperature=0.8,
        max_tokens=4096
    )
    return chat.choices[0].message.content

def call_deepseek(prompt, system_prompt=''):
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    else:
        messages.append({'role': 'system', 'content': 'You are a helpful, intelligent AI assistant. Answer naturally and completely.'})
    messages.append({'role': 'user', 'content': prompt})
    
    res = requests.post(
        'https://api.deepseek.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {DEEPSEEK_KEY}', 'Content-Type': 'application/json'},
        json={'model': 'deepseek-chat', 'messages': messages, 'temperature': 0.8, 'max_tokens': 4096},
        timeout=120
    )
    return res.json()['choices'][0]['message']['content']

def call_gemini(prompt, system_prompt=''):
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\nUser: {prompt}"
    
    res = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_KEY}',
        json={'contents': [{'parts': [{'text': full_prompt}]}], 'generationConfig': {'temperature': 0.8, 'maxOutputTokens': 4096}},
        timeout=60
    )
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# ============ MODELS ============

@app.route('/models', methods=['GET'])
def list_models():
    return jsonify({'models': [
        {'id': 'groq', 'name': '⚡ Groq (Llama 3.1 70B)', 'speed': 'Fastest', 'free': True, 'default': True},
        {'id': 'deepseek', 'name': '🚀 DeepSeek-Chat', 'speed': 'Fast', 'free': True},
        {'id': 'gemini', 'name': '🧠 Google Gemini Pro', 'speed': 'Medium', 'free': True}
    ]})

# ============ HISTORY ============

@app.route('/history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 20, type=int)
    return jsonify({'total': len(history), 'history': history[-limit:]})

@app.route('/history/clear', methods=['POST'])
def clear_history():
    global history
    history = []
    return jsonify({'message': 'History cleared'})

# ============ ZIP DOWNLOAD ============

@app.route('/download_zip', methods=['POST'])
def download_zip():
    files = request.json.get('files', {})
    if not files:
        return jsonify({'error': 'No files'}), 400
    
    tmp = tempfile.mkdtemp()
    zp = os.path.join(tmp, f"ghost_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            zf.write(path, name)
    
    return send_file(zp, as_attachment=True, download_name='code.zip')

# ============ STATS ============

@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        'total_requests': len(history),
        'total_users': len(users),
        'active_ips': len(request_log),
        'uptime': 'running'
    })

# ============ MAIN ============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f'👻 Ghost AI starting on port {port}')
    app.run(host='0.0.0.0', port=port)
