from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import Config
from models import db, Appointment
from datetime import datetime
import requests

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

def verify_user_with_service(user_id, token):
    """Verify user exists via User Service"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f"{app.config['USER_SERVICE_URL']}/users/{user_id}",
            headers=headers,
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

@app.route('/appointments/book', methods=['POST'])
@jwt_required()
def book_appointment():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    token = request.headers.get('Authorization', '').split(' ')[1] if 'Authorization' in request.headers else None
    
    if not data or not data.get('doctor_id') or not data.get('appointment_date'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        appointment_date = datetime.fromisoformat(data['appointment_date'])
    except ValueError:
        return jsonify({'message': 'Invalid datetime format'}), 400
    
    # Check for double booking
    existing = Appointment.query.filter(
        Appointment.patient_id == current_user_id,
        Appointment.doctor_id == data['doctor_id'],
        Appointment.appointment_date == appointment_date,
        Appointment.status != 'cancelled'
    ).first()
    
    if existing:
        return jsonify({'message': 'Appointment slot already booked'}), 409
    
    appointment = Appointment(
        patient_id=current_user_id,
        doctor_id=data['doctor_id'],
        appointment_date=appointment_date,
        status='pending',
        reason=data.get('reason')
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment booked successfully',
        'appointment': appointment.to_dict()
    }), 201

@app.route('/appointments/history', methods=['GET'])
@jwt_required()
def get_appointment_history():
    current_user_id = get_jwt_identity()
    
    appointments = Appointment.query.filter_by(patient_id=current_user_id).all()
    
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
    
    appointment.status = 'confirmed'
    appointment.notes = request.get_json().get('notes') if request.get_json() else None
    db.session.commit()
    
    return jsonify({
        'message': 'Appointment confirmed',
        'appointment': appointment.to_dict()
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Appointment Service is healthy'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5002)
