from flask import Blueprint, request, jsonify
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

ADMIN_TOKEN = 'mysecret123'

def verify_admin(req):
    return req.headers.get('X-Admin-Token') == ADMIN_TOKEN

@admin_bp.route('/stats', methods=['GET'])
def admin_stats():
    if not verify_admin(request):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'total_users': 0,
        'total_generations': 0,
        'active_today': 0,
        'server_uptime': '24h',
        'timestamp': datetime.now().isoformat()
    })

@admin_bp.route('/users', methods=['GET'])
def admin_users():
    if not verify_admin(request):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'users': [], 'total': 0})

@admin_bp.route('/logs', methods=['GET'])
def admin_logs():
    if not verify_admin(request):
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'logs': [], 'total': 0})