from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.calorie_service import calculate_daily_budget
import bcrypt
import os
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'Email, password, and name are required'}), 400

    # Check if user already exists
    existing = UserRepository.get_by_email(data['email'])
    if existing:
        return jsonify({'error': 'Email already registered'}), 409

    # Hash password
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        email=data['email'],
        password_hash=password_hash,
        name=data['name'],
    )

    UserRepository.create(user)

    access_token = create_access_token(identity=user.id)

    return jsonify({
        'message': 'Registration successful',
        'token': access_token,
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = UserRepository.get_by_email(data['email'])
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify({
        'message': 'Login successful',
        'token': access_token,
        'user': user.to_dict()
    }), 200

@auth_bp.route('/google', methods=['POST'])
def google_login():
    """Login or register with Google."""
    data = request.get_json()
    token = data.get('credential')

    if not token:
        return jsonify({'error': 'No token provided'}), 400

    try:
        # Verify Google token
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID")
        # To tolerate dummy tokens during dev without Google setup:
        if client_id == "YOUR_GOOGLE_CLIENT_ID" and token == "dummy-google-token":
            idinfo = {"email": "google.user@example.com", "name": "Google User"}
        else:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)

        email = idinfo['email']
        name = idinfo.get('name', 'User')
        
        user = UserRepository.get_by_email(email)
        
        if not user:
            # Create a random password for google users
            random_pass = bcrypt.hashpw(os.urandom(24), bcrypt.gensalt()).decode('utf-8')
            user = User(
                email=email,
                password_hash=random_pass,
                name=name
            )
            UserRepository.create(user)

        access_token = create_access_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'token': access_token,
            'user': user.to_dict()
        }), 200

    except ValueError:
        return jsonify({'error': 'Invalid Google token'}), 401


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile."""
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile and calculate calorie budget."""
    user_id = get_jwt_identity()
    user = UserRepository.get_by_id(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()

    # Update profile fields
    if 'name' in data:
        user.name = data['name']
    if 'age' in data:
        user.age = data['age']
    if 'gender' in data:
        user.gender = data['gender']
    if 'weight_kg' in data:
        user.weight_kg = data['weight_kg']
    if 'height_cm' in data:
        user.height_cm = data['height_cm']
    if 'activity_level' in data:
        user.activity_level = data['activity_level']
    if 'goal' in data:
        user.goal = data['goal']

    # Calculate daily calorie budget if we have all required fields
    if all([user.weight_kg, user.height_cm, user.age, user.gender, user.activity_level, user.goal]):
        user.daily_calorie_budget = calculate_daily_budget(
            user.weight_kg, user.height_cm, user.age,
            user.gender, user.activity_level, user.goal
        )
        user.profile_completed = True

    UserRepository.commit()

    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    }), 200
