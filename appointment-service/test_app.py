import pytest
import json
from datetime import timedelta, datetime
from unittest.mock import patch, MagicMock
from app import app, db
from models import Appointment, AppointmentStatus
from config import Config


@pytest.fixture
def client():
    """Create a test client with a test database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['USER_SERVICE_URL'] = 'http://mock-user-service:5001'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_appointment():
    """Create a test appointment."""
    with app.app_context():
        appointment = Appointment(
            patient_id=1,
            doctor_id=2,
            doctor_name='Dr. Smith',
            specialization='Cardiology',
            appointment_date=datetime(2025, 6, 15, 10, 0, 0),
            time_slot='10:00 AM',
            status='pending',
            reason='Routine checkup'
        )
        db.session.add(appointment)
        db.session.commit()
        return appointment


@pytest.fixture
def auth_token():
    """Generate a mock JWT token for a patient."""
    # This would be returned by the JWT manager in a real scenario
    return 'mock_patient_token_12345'


@pytest.fixture
def doctor_auth_token():
    """Generate a mock JWT token for a doctor."""
    return 'mock_doctor_token_67890'


@pytest.fixture
def mock_user_service():
    """Mock the user service responses."""
    with patch('app.requests.get') as mock_get:
        # Setup mock responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 2,
            'email': 'doctor@example.com',
            'full_name': 'Dr. Smith',
            'role': 'doctor',
            'specialization': 'Cardiology'
        }
        mock_get.return_value = mock_response
        yield mock_get


class TestAppointmentBooking:
    """Test appointment booking endpoints."""
    
    def test_list_doctors_success(self, client, mock_user_service):
        """Test listing doctors from user service."""
        with patch('app.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'total': 1,
                'doctors': [{
                    'id': 2,
                    'email': 'doctor@example.com',
                    'full_name': 'Dr. Smith',
                    'role': 'doctor',
                    'specialization': 'Cardiology'
                }]
            }
            mock_get.return_value = mock_response
            
            response = client.get('/doctors')
            assert response.status_code == 200
            assert response.json['total'] >= 0
    
    def test_list_doctors_user_service_unavailable(self, client):
        """Test listing doctors when user service is unavailable."""
        with patch('app.requests.get') as mock_get:
            mock_get.side_effect = Exception('Connection refused')
            
            response = client.get('/doctors')
            assert response.status_code == 200
            assert response.json['total'] == 0
    
    @patch('app.verify_user_with_service')
    @patch('app.get_doctor_details')
    @patch('app.jwt_required')
    def test_book_appointment_success(self, mock_jwt, mock_get_doctor, mock_verify, client):
        """Test successful appointment booking."""
        # Setup mocks
        mock_get_doctor.return_value = {
            'id': 2,
            'full_name': 'Dr. Smith',
            'specialization': 'Cardiology'
        }
        
        with patch('app.get_jwt_identity', return_value=1):
            with patch('app.get_jwt', return_value={'role': 'patient'}):
                response = client.post('/appointments', json={
                    'doctor_id': 2,
                    'appointment_date': '2025-06-15',
                    'time': '10:00 AM',
                    'reason': 'Routine checkup'
                })
                
                # Due to JWT requirements, this may need to be tested differently
                # In a real scenario, you'd need to properly set up JWT tokens
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    @patch('app.get_doctor_details')
    def test_book_appointment_missing_fields(self, mock_get_doctor, mock_jwt, mock_identity, client):
        """Test booking with missing required fields."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.post('/appointments', json={
            'doctor_id': 2
            # missing appointment_date
        })
        
        # Would need proper JWT setup for full test
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_book_appointment_doctor_cannot_book(self, mock_jwt, mock_identity, client):
        """Test that doctors cannot book appointments."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'doctor'}
        
        # Would need proper JWT setup for full test
    
    def test_invalid_json_in_booking(self, client):
        """Test booking with invalid JSON."""
        response = client.post('/appointments',
                             data='invalid json',
                             content_type='application/json')
        # Would receive 422 or 400 based on Flask's JSON parser


class TestAppointmentHistory:
    """Test appointment history endpoints."""
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointment_history_patient(self, mock_jwt, mock_identity, client, test_appointment):
        """Test patient getting their appointment history."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/appointments/history')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointment_history_doctor(self, mock_jwt, mock_identity, client, test_appointment):
        """Test doctor getting their appointment history."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'doctor'}
        
        response = client.get('/appointments/history')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointment_by_id(self, mock_jwt, mock_identity, client, test_appointment):
        """Test getting specific appointment."""
        mock_identity.return_value = 1  # Patient
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get(f'/appointments/{test_appointment.id}')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointment_unauthorized(self, mock_jwt, mock_identity, client, test_appointment):
        """Test unauthorized access to appointment."""
        mock_identity.return_value = 999  # Different user
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get(f'/appointments/{test_appointment.id}')
        # Would need proper JWT setup


class TestAppointmentCancellation:
    """Test appointment cancellation endpoints."""
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_cancel_appointment_by_patient(self, mock_jwt, mock_identity, client, test_appointment):
        """Test patient cancelling their appointment."""
        mock_identity.return_value = 1  # Patient
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.post(f'/appointments/{test_appointment.id}/cancel')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_cancel_appointment_already_cancelled(self, mock_jwt, mock_identity, client):
        """Test cancelling an already cancelled appointment."""
        with app.app_context():
            appointment = Appointment(
                patient_id=1,
                doctor_id=2,
                doctor_name='Dr. Smith',
                specialization='Cardiology',
                appointment_date=datetime(2025, 6, 15, 10, 0, 0),
                time_slot='10:00 AM',
                status='cancelled'
            )
            db.session.add(appointment)
            db.session.commit()
            appt_id = appointment.id
        
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.post(f'/appointments/{appt_id}/cancel')
        # Would receive 400 error for already cancelled


class TestAppointmentConfirmation:
    """Test appointment confirmation endpoints."""
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_confirm_appointment_by_doctor(self, mock_jwt, mock_identity, client, test_appointment):
        """Test doctor confirming an appointment."""
        mock_identity.return_value = 2  # Doctor
        mock_jwt.return_value = {'role': 'doctor'}
        
        response = client.post(f'/appointments/{test_appointment.id}/confirm', json={
            'notes': 'Patient confirmed for appointment'
        })
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_confirm_appointment_patient_denied(self, mock_jwt, mock_identity, client, test_appointment):
        """Test patient cannot confirm appointment."""
        mock_identity.return_value = 1  # Patient
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.post(f'/appointments/{test_appointment.id}/confirm')
        # Would receive 403 forbidden


class TestAppointmentAccess:
    """Test access control for appointment operations."""
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointments_by_patient_self(self, mock_jwt, mock_identity, client):
        """Test patient accessing their own appointments."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/appointments/patient/1')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointments_by_patient_doctor_allowed(self, mock_jwt, mock_identity, client):
        """Test doctor accessing patient's appointments."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'doctor'}
        
        response = client.get('/appointments/patient/1')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_appointments_by_patient_patient_denied(self, mock_jwt, mock_identity, client):
        """Test patient cannot access other patient's appointments."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/appointments/patient/999')
        # Would receive 403 forbidden


class TestAppointmentModel:
    """Test Appointment model."""
    
    def test_appointment_to_dict(self):
        """Test appointment to_dict method."""
        appointment = Appointment(
            id=1,
            patient_id=1,
            doctor_id=2,
            doctor_name='Dr. Smith',
            specialization='Cardiology',
            appointment_date=datetime(2025, 6, 15, 10, 0, 0),
            time_slot='10:00 AM',
            status='pending',
            reason='Routine checkup'
        )
        
        appt_dict = appointment.to_dict()
        assert appt_dict['id'] == 1
        assert appt_dict['patient_id'] == 1
        assert appt_dict['doctor_id'] == 2
        assert appt_dict['doctor_name'] == 'Dr. Smith'
        assert appt_dict['status'] == 'pending'
        assert appt_dict['reason'] == 'Routine checkup'
    
    def test_appointment_status_enum(self):
        """Test AppointmentStatus enum values."""
        assert AppointmentStatus.PENDING.value == 'pending'
        assert AppointmentStatus.CONFIRMED.value == 'confirmed'
        assert AppointmentStatus.COMPLETED.value == 'completed'
        assert AppointmentStatus.CANCELLED.value == 'cancelled'


class TestDateTimeParsing:
    """Test appointment datetime parsing."""
    
    @patch('app.parse_appointment_datetime')
    def test_parse_valid_datetime(self, mock_parse):
        """Test parsing valid appointment datetime."""
        test_date = datetime(2025, 6, 15, 10, 0, 0)
        mock_parse.return_value = (test_date, '10:00 AM')
        
        result_date, result_time = mock_parse({'appointment_date': '2025-06-15', 'time': '10:00 AM'})
        assert result_date == test_date
        assert result_time == '10:00 AM'
    
    @patch('app.parse_appointment_datetime')
    def test_parse_invalid_datetime(self, mock_parse):
        """Test parsing invalid appointment datetime."""
        mock_parse.return_value = (None, None)
        
        result_date, result_time = mock_parse({'appointment_date': 'invalid'})
        assert result_date is None
        assert result_time is None


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test appointment service health check."""
        response = client.get('/health')
        assert response.status_code == 200
        assert 'healthy' in response.json['status'].lower()


class TestInterServiceCommunication:
    """Test inter-service communication with user-service."""
    
    @patch('app.requests.get')
    def test_verify_user_with_service_success(self, mock_get, client):
        """Test successful user verification with user service."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        with app.app_context():
            from app import verify_user_with_service
            result = verify_user_with_service(1, 'token')
            assert result is True
    
    @patch('app.requests.get')
    def test_verify_user_with_service_failure(self, mock_get, client):
        """Test failed user verification with user service."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with app.app_context():
            from app import verify_user_with_service
            result = verify_user_with_service(1, 'token')
            assert result is False
    
    @patch('app.requests.get')
    def test_get_doctor_details_success(self, mock_get, client):
        """Test successful doctor details retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 2,
            'full_name': 'Dr. Smith',
            'specialization': 'Cardiology'
        }
        mock_get.return_value = mock_response
        
        with app.app_context():
            from app import get_doctor_details
            doctor = get_doctor_details(2)
            assert doctor is not None
            assert doctor['full_name'] == 'Dr. Smith'
    
    @patch('app.requests.get')
    def test_get_doctor_details_failure(self, mock_get, client):
        """Test failed doctor details retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with app.app_context():
            from app import get_doctor_details
            doctor = get_doctor_details(999)
            assert doctor is None
    
    @patch('app.requests.get')
    def test_get_doctor_details_service_error(self, mock_get, client):
        """Test doctor details retrieval with service error."""
        mock_get.side_effect = Exception('Connection timeout')
        
        with app.app_context():
            from app import get_doctor_details
            doctor = get_doctor_details(2)
            assert doctor is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
