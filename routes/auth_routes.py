from flask import Blueprint, request, jsonify
from models.user import User
import hashlib

auth_bp = Blueprint('auth', __name__)

# Simple in-memory store (use DB in production)
users_store = {}

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    name = data.get('name', '')
    
    if email in users_store:
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(email, name)
    users_store[email] = {
        'user': user,
        'password': hashlib.sha256(password.encode()).hexdigest()
    }
    
    return jsonify({'message': 'Registered!', 'user': user.to_dict()})

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '')
    password = data.get('password', '')
    
    stored = users_store.get(email)
    if not stored:
        return jsonify({'error': 'User not found'}), 404
    
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if stored['password'] != hashed:
        return jsonify({'error': 'Invalid password'}), 401
    
    user = stored['user']
    user.last_login = __import__('datetime').datetime.now().isoformat()
    
    return jsonify({'message': 'Logged in!', 'user': user.to_dict()})