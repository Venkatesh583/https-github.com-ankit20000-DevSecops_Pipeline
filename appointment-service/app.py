import logging
import os
import time

import requests
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required
from datetime import datetime

from config import Config
from models import Appointment, db
from observability import configure_observability, log_event

app = Flask(__name__)
app.config.from_object(Config)
app.config['SERVICE_NAME'] = os.getenv('OTEL_SERVICE_NAME', 'appointment-service')
CORS(app, origins="*")

db.init_app(app)
jwt = JWTManager(app)
configure_observability(app, app.config['SERVICE_NAME'])

def verify_user_with_service(user_id, token):
    """Verify user exists via User Service"""
    url = f"{app.config['USER_SERVICE_URL']}/users/{user_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Request-ID': getattr(g, 'request_id', None)
    }
    start = time.monotonic()
    try:
        response = requests.get(url, headers=headers, timeout=5)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_event(logging.INFO, 'user_service_lookup', request_id=getattr(g, 'request_id', None), remote_url=url, remote_method='GET', status_code=response.status_code, duration_ms=duration_ms)
        return response.status_code == 200
    except requests.RequestException as exc:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_event(logging.WARNING, 'user_service_lookup_failed', request_id=getattr(g, 'request_id', None), remote_url=url, remote_method='GET', duration_ms=duration_ms, error=str(exc))
        return False


def get_doctor_details(doctor_id):
    url = f"{app.config['USER_SERVICE_URL']}/doctors/{doctor_id}"
    start = time.monotonic()
    try:
        response = requests.get(url, timeout=5)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_event(logging.INFO, 'doctor_lookup', request_id=getattr(g, 'request_id', None), remote_url=url, remote_method='GET', status_code=response.status_code, duration_ms=duration_ms)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as exc:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_event(logging.WARNING, 'doctor_lookup_failed', request_id=getattr(g, 'request_id', None), remote_url=url, remote_method='GET', duration_ms=duration_ms, error=str(exc))
    return None


def parse_appointment_datetime(data):
    appointment_date = data.get('appointment_date')
    if not appointment_date:
        return None, None

    time_slot = data.get('time')
    if time_slot:
        try:
            appointment_datetime = datetime.strptime(
                f"{appointment_date} {time_slot}",
                '%Y-%m-%d %I:%M %p'
            )
        except ValueError:
            return None, None
    else:
        try:
            appointment_datetime = datetime.fromisoformat(appointment_date)
            time_slot = appointment_datetime.strftime('%I:%M %p')
        except ValueError:
            return None, None

    return appointment_datetime, time_slot


@app.route('/doctors', methods=['GET'])
def list_doctors():
    url = f"{app.config['USER_SERVICE_URL']}/doctors"
    start = time.monotonic()
    doctors = []
    try:
        response = requests.get(url, timeout=5)
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_event(logging.INFO, 'doctor_listing', request_id=getattr(g, 'request_id', None), remote_url=url, remote_method='GET', status_code=response.status_code, duration_ms=duration_ms)
        if response.status_code == 200:
            doctors = response.json().get('doctors', [])
    except requests.RequestException as exc:
        duration_ms = round((time.monotonic() - start) * 1000, 2)
        log_event(logging.WARNING, 'doctor_listing_failed', request_id=getattr(g, 'request_id', None), remote_url=url, remote_method='GET', duration_ms=duration_ms, error=str(exc))

    return jsonify({'total': len(doctors), 'doctors': doctors}), 200


@app.route('/appointments', methods=['POST'])
@app.route('/appointments/book', methods=['POST'])
@jwt_required()
def book_appointment():
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    data = request.get_json(silent=True)
    
    if not isinstance(data, dict):
        return jsonify({'error': 'validation_error', 'message': 'Request body must be JSON', 'request_id': getattr(g, 'request_id', None)}), 400

    if not data.get('doctor_id') or not data.get('appointment_date'):
        return jsonify({'error': 'validation_error', 'message': 'Missing required fields', 'request_id': getattr(g, 'request_id', None)}), 400

    if jwt_data.get('role') == 'doctor':
        log_event(logging.WARNING, 'doctor_booking_attempt_blocked', request_id=getattr(g, 'request_id', None), user_id=current_user_id)
        return jsonify({'message': 'Only patients can book appointments'}), 403

    doctor = get_doctor_details(data['doctor_id'])
    if not doctor:
        log_event(logging.WARNING, 'doctor_not_found_for_booking', request_id=getattr(g, 'request_id', None), doctor_id=data['doctor_id'])
        return jsonify({'message': 'Doctor not found'}), 404

    appointment_datetime, time_slot = parse_appointment_datetime(data)
    if not appointment_datetime:
        return jsonify({'error': 'validation_error', 'message': 'Invalid date or time format', 'request_id': getattr(g, 'request_id', None)}), 400

    existing = Appointment.query.filter(
        Appointment.patient_id == current_user_id,
        Appointment.doctor_id == data['doctor_id'],
        Appointment.appointment_date == appointment_datetime,
        Appointment.status != 'cancelled'
    ).first()
    
    if existing:
        log_event(logging.WARNING, 'duplicate_appointment_attempt', request_id=getattr(g, 'request_id', None), patient_id=current_user_id, doctor_id=data['doctor_id'])
        return jsonify({'message': 'Appointment slot already booked'}), 409
    
    appointment = Appointment(
        patient_id=current_user_id,
        doctor_id=data['doctor_id'],
        doctor_name=doctor.get('full_name'),
        specialization=doctor.get('specialization'),
        appointment_date=appointment_datetime,
        time_slot=time_slot,
        status='pending',
        reason=data.get('reason')
    )
    
    db.session.add(appointment)
    db.session.commit()
    log_event(logging.INFO, 'appointment_booked', request_id=getattr(g, 'request_id', None), appointment_id=appointment.id, patient_id=current_user_id, doctor_id=data['doctor_id'])
    
    return jsonify({
        'message': 'Appointment booked successfully',
        'appointment': appointment.to_dict()
    }), 201

@app.route('/appointments/history', methods=['GET'])
@jwt_required()
def get_appointment_history():
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    role = jwt_data.get('role')

    if role == 'doctor':
        appointments = Appointment.query.filter_by(doctor_id=current_user_id).all()
    else:
        appointments = Appointment.query.filter_by(patient_id=current_user_id).all()

    log_event(logging.DEBUG, 'appointment_history_retrieved', request_id=getattr(g, 'request_id', None), user_id=current_user_id, role=role, total=len(appointments))
    
    return jsonify({
        'total': len(appointments),
        'appointments': [a.to_dict() for a in appointments]
    }), 200

@app.route('/appointments/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_appointment(appointment_id):
    current_user_id = get_jwt_identity()
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404
    
    if appointment.patient_id != current_user_id and appointment.doctor_id != current_user_id:
        return jsonify({'message': 'Access forbidden'}), 403
    
    return jsonify(appointment.to_dict()), 200

@app.route('/appointments/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def get_appointments_by_patient(patient_id):
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    role = jwt_data.get('role')

    if current_user_id != patient_id and role != 'doctor':
        return jsonify({'message': 'Access forbidden'}), 403

    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    return jsonify({
        'total': len(appointments),
        'appointments': [a.to_dict() for a in appointments]
    }), 200

@app.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(appointment_id):
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    role = jwt_data.get('role')
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404
    
    if appointment.patient_id != current_user_id and appointment.doctor_id != current_user_id and role != 'admin':
        return jsonify({'message': 'Access forbidden'}), 403
    
    if appointment.status == 'cancelled':
        return jsonify({'message': 'Appointment already cancelled'}), 400
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment cancelled',
        'appointment': appointment.to_dict()
    }), 200

@app.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_appointment(appointment_id):
    current_user_id = get_jwt_identity()
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404
    
    if appointment.patient_id != current_user_id:
        return jsonify({'message': 'Access forbidden'}), 403
    
    if appointment.status == 'cancelled':
        return jsonify({'message': 'Appointment already cancelled'}), 400
    
    if appointment.status == 'completed':
        return jsonify({'message': 'Cannot cancel completed appointment'}), 400
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment cancelled',
        'appointment': appointment.to_dict()
    }), 200

@app.route('/appointments/<int:appointment_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_appointment(appointment_id):
    current_user_id = get_jwt_identity()
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'message': 'Appointment not found'}), 404
    
    if appointment.doctor_id != current_user_id:
        return jsonify({'message': 'Access forbidden'}), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    
    appointment.status = 'confirmed'
    appointment.notes = payload.get('notes')
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment confirmed',
        'appointment': appointment.to_dict()
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    log_event(logging.INFO, 'health_check', request_id=getattr(g, 'request_id', None), service=app.config['SERVICE_NAME'])
    return jsonify({'status': 'Appointment Service is healthy'}), 200


@app.errorhandler(404)
def handle_not_found(error):
    return jsonify({'error': 'not_found', 'message': 'Resource not found', 'request_id': getattr(g, 'request_id', None)}), 404


@app.errorhandler(Exception)
def handle_exception(error):
    log_event(logging.ERROR, 'unhandled_exception', request_id=getattr(g, 'request_id', None), path=request.path, method=request.method, error=str(error))
    return jsonify({'error': 'internal_server_error', 'message': 'Internal server error', 'request_id': getattr(g, 'request_id', None)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=5002)
