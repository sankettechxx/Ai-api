from flask import Blueprint, request, jsonify
import json
import hashlib
import base64
import uuid

tool_bp = Blueprint('tools', __name__)

@tool_bp.route('/json', methods=['POST'])
def format_json():
    try:
        data = json.loads(request.json['data'])
        return jsonify({'result': json.dumps(data, indent=2)})
    except:
        return jsonify({'error': 'Invalid JSON'})

@tool_bp.route('/base64_encode', methods=['POST'])
def base64_encode_route():
    text = request.json.get('data', '')
    return jsonify({'result': base64.b64encode(text.encode()).decode()})

@tool_bp.route('/base64_decode', methods=['POST'])
def base64_decode_route():
    try:
        text = request.json.get('data', '')
        return jsonify({'result': base64.b64decode(text).decode()})
    except:
        return jsonify({'error': 'Invalid Base64'})

@tool_bp.route('/hash', methods=['POST'])
def hash_route():
    text = request.json.get('data', '')
    return jsonify({
        'md5': hashlib.md5(text.encode()).hexdigest(),
        'sha256': hashlib.sha256(text.encode()).hexdigest()
    })

@tool_bp.route('/uuid', methods=['GET'])
def uuid_route():
    return jsonify({'result': str(uuid.uuid4())})

@tool_bp.route('/password', methods=['GET'])
def password_route():
    import random
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%'
    pwd = ''.join(random.choice(chars) for _ in range(16))
    return jsonify({'result': pwd})