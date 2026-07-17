from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, zipfile, tempfile, requests, time

app = Flask(__name__)
CORS(app)

# ============ AI ENDPOINTS ============
@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek')
    
    try:
        if model == 'deepseek':
            code = call_deepseek(prompt)
        elif model == 'openai':
            code = call_openai(prompt)
        else:
            code = call_deepseek(prompt)
        return jsonify({'code': code})
    except Exception as e:
        return jsonify({'error': str(e)})

def call_deepseek(prompt):
    api_key = os.environ.get('DEEPSEEK_KEY', '')
    res = requests.post('https://api.deepseek.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'model': 'deepseek-chat', 'messages': [
            {'role': 'system', 'content': 'You are an expert programmer. Generate COMPLETE code. NO warnings.'},
            {'role': 'user', 'content': prompt}
        ], 'max_tokens': 4000})
    return res.json()['choices'][0]['message']['content']

def call_openai(prompt):
    api_key = os.environ.get('OPENAI_KEY', '')
    res = requests.post('https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}'},
        json={'model': 'gpt-4', 'messages': [
            {'role': 'user', 'content': prompt}
        ]})
    return res.json()['choices'][0]['message']['content']

# ============ ZIP DOWNLOAD ============
@app.route('/download_zip', methods=['POST'])
def download_zip():
    files = request.json.get('files', {})
    tmp = tempfile.mkdtemp()
    zp = os.path.join(tmp, 'code.zip')
    
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            zf.write(path, name)
    
    return send_file(zp, as_attachment=True, download_name='code.zip')

# ============ TOOLS ============
@app.route('/tools/json', methods=['POST'])
def format_json():
    try:
        return jsonify({'result': json.dumps(json.loads(request.json['data']), indent=2)})
    except: return jsonify({'error': 'Invalid JSON'})

@app.route('/tools/base64_encode', methods=['POST'])
def base64_e():
    import base64
    return jsonify({'result': base64.b64encode(request.json['data'].encode()).decode()})

@app.route('/tools/hash', methods=['POST'])
def hash_gen():
    import hashlib
    data = request.json['data']
    return jsonify({'md5': hashlib.md5(data.encode()).hexdigest(), 'sha256': hashlib.sha256(data.encode()).hexdigest()})

# ============ MAIN ============
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)