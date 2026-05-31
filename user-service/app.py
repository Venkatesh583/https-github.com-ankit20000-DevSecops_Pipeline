import logging
import os
import re

from flask import Flask, g, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError

from config import Config
from models import User, db
from observability import configure_observability, log_event

app = Flask(__name__)
app.config.from_object(Config)

app.config['SERVICE_NAME'] = os.getenv('OTEL_SERVICE_NAME', 'user-service')
db.init_app(app)
jwt = JWTManager(app)
logger = configure_observability(app, app.config['SERVICE_NAME'])

ALLOWED_ROLES = {'patient', 'doctor', 'admin'}
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def role_required(roles):
    def decorator(fn):
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            if user is None:
                return jsonify({'message': 'User not found'}), 404
            if user.role not in roles:
                return jsonify({'message': 'Access forbidden'}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'validation_error', 'message': 'Request body must be JSON', 'request_id': getattr(g, 'request_id', None)}), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    full_name = (data.get('full_name') or '').strip()

    if not email or not password or not full_name:
        return jsonify({'error': 'validation_error', 'message': 'Missing required fields', 'request_id': getattr(g, 'request_id', None)}), 400
    if not EMAIL_PATTERN.match(email):
        return jsonify({'error': 'validation_error', 'message': 'Invalid email format', 'request_id': getattr(g, 'request_id', None)}), 400
    if len(password) < 8:
        return jsonify({'error': 'validation_error', 'message': 'Password must be at least 8 characters long', 'request_id': getattr(g, 'request_id', None)}), 400

    role = data.get('role', 'patient')
    if role not in ALLOWED_ROLES:
        return jsonify({'error': 'validation_error', 'message': 'Unsupported role', 'request_id': getattr(g, 'request_id', None)}), 400

    if User.query.filter_by(email=email).first():
        log_event(logging.WARNING, 'duplicate_registration_attempt', request_id=getattr(g, 'request_id', None), email=email)
        return jsonify({'message': 'Email already registered'}), 409

    user = User(
        email=email,
        full_name=full_name,
        role=role,
        phone=data.get('phone'),
        specialization=data.get('specialization')
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        log_event(logging.ERROR, 'database_integrity_error', request_id=getattr(g, 'request_id', None), email=email)
        return jsonify({'error': 'database_error', 'message': 'Failed to register user', 'request_id': getattr(g, 'request_id', None)}), 500

    log_event(logging.INFO, 'user_registered', request_id=getattr(g, 'request_id', None), user_id=user.id, email=email, role=role)
    return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'validation_error', 'message': 'Request body must be JSON', 'request_id': getattr(g, 'request_id', None)}), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({'error': 'validation_error', 'message': 'Missing credentials', 'request_id': getattr(g, 'request_id', None)}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        log_event(logging.WARNING, 'failed_login_attempt', request_id=getattr(g, 'request_id', None), email=email)
        return jsonify({'message': 'Invalid credentials'}), 401

    if not user.is_active:
        log_event(logging.WARNING, 'inactive_login_attempt', request_id=getattr(g, 'request_id', None), user_id=user.id, email=email)
        return jsonify({'message': 'Account is inactive'}), 403

    access_token = create_access_token(identity=user.id, additional_claims={'role': user.role})
    log_event(logging.INFO, 'user_login_success', request_id=getattr(g, 'request_id', None), user_id=user.id, email=email, role=user.role)
    return jsonify({'message': 'Login successful', 'access_token': access_token, 'user': user.to_dict()}), 200


@app.route('/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user.to_dict()), 200


@app.route('/profile/<int:user_id>', methods=['GET'])
@jwt_required()
def get_profile_by_id(user_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    requesting_user = User.query.get(current_user_id)

    if not requesting_user:
        return jsonify({'message': 'User not found'}), 404

    if current_user_id != user_id and requesting_user.role not in ['admin', 'doctor']:
        return jsonify({'message': 'Access forbidden'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user.to_dict()), 200


@app.route('/users/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'validation_error', 'message': 'Request body must be JSON', 'request_id': getattr(g, 'request_id', None)}), 400

    user.full_name = data.get('full_name', user.full_name)
    user.phone = data.get('phone', user.phone)

    db.session.commit()
    log_event(logging.INFO, 'profile_updated', request_id=getattr(g, 'request_id', None), user_id=user.id)
    return jsonify({'message': 'Profile updated', 'user': user.to_dict()}), 200


@app.route('/doctors', methods=['GET'])
def list_doctors():
    doctors = User.query.filter_by(role='doctor').all()
    return jsonify({'total': len(doctors), 'doctors': [doctor.to_dict() for doctor in doctors]}), 200


@app.route('/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
    if not doctor:
        log_event(logging.WARNING, 'doctor_not_found', request_id=getattr(g, 'request_id', None), doctor_id=doctor_id)
        return jsonify({'message': 'Doctor not found'}), 404
    return jsonify(doctor.to_dict()), 200


@app.route('/users/<int:user_id>', methods=['GET'])
@role_required(['admin', 'doctor'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user.to_dict()), 200


@app.route('/health', methods=['GET'])
def health_check():
    log_event(logging.INFO, 'health_check', request_id=getattr(g, 'request_id', None), service=app.config['SERVICE_NAME'])
    return jsonify({'status': 'User Service is healthy'}), 200


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=5001)
