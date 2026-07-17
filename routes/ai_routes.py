from flask import Blueprint, request, jsonify
from utils.ai_manager import AIManager
from utils.zip_creator import ZipCreator

ai_bp = Blueprint('ai', __name__)
ai_manager = AIManager()

@ai_bp.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek')
    api_keys = data.get('api_keys', {})
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        code = ai_manager.generate(prompt, model, api_keys)
        return jsonify({'code': code, 'model': model})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_bp.route('/models', methods=['GET'])
def list_models():
    return jsonify({
        'models': [
            {'id': 'deepseek', 'name': 'DeepSeek-Coder', 'free': True},
            {'id': 'openai', 'name': 'GPT-4', 'free': False},
            {'id': 'claude', 'name': 'Claude 3', 'free': False},
            {'id': 'qwen', 'name': 'Qwen Coder', 'free': True}
        ]
    })

@ai_bp.route('/download_zip', methods=['POST'])
def download_zip():
    files = request.json.get('files', {})
    if not files:
        return jsonify({'error': 'No files provided'}), 400
    
    zip_path = ZipCreator.create(files)
    return send_file(zip_path, as_attachment=True, download_name='code.zip')