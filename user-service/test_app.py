import pytest
import json
from datetime import timedelta
from app import app, db
from models import User
from config import Config


@pytest.fixture
def client():
    """Create a test client with a test database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user():
    """Create a test user."""
    with app.app_context():
        user = User(
            email='testuser@example.com',
            full_name='Test User',
            role='patient',
            phone='1234567890'
        )
        user.set_password('testpassword123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_doctor():
    """Create a test doctor."""
    with app.app_context():
        doctor = User(
            email='doctor@example.com',
            full_name='Dr. Smith',
            role='doctor',
            phone='0987654321',
            specialization='Cardiology'
        )
        doctor.set_password('doctorpass123')
        db.session.add(doctor)
        db.session.commit()
        return doctor


@pytest.fixture
def test_admin():
    """Create a test admin user."""
    with app.app_context():
        admin = User(
            email='admin@example.com',
            full_name='Admin User',
            role='admin',
            phone='5555555555'
        )
        admin.set_password('adminpass123')
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def auth_token(client, test_user):
    """Generate a JWT token for test user."""
    response = client.post('/login', json={
        'email': 'testuser@example.com',
        'password': 'testpassword123'
    })
    return response.json['access_token']


@pytest.fixture
def doctor_auth_token(client, test_doctor):
    """Generate a JWT token for test doctor."""
    response = client.post('/login', json={
        'email': 'doctor@example.com',
        'password': 'doctorpass123'
    })
    return response.json['access_token']


@pytest.fixture
def admin_auth_token(client, test_admin):
    """Generate a JWT token for test admin."""
    response = client.post('/login', json={
        'email': 'admin@example.com',
        'password': 'adminpass123'
    })
    return response.json['access_token']


class TestUserRegistration:
    """Test user registration endpoint."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post('/register', json={
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'full_name': 'New User',
            'role': 'patient'
        })
        assert response.status_code == 201
        assert response.json['message'] == 'User registered successfully'
        assert response.json['user']['email'] == 'newuser@example.com'
        assert response.json['user']['role'] == 'patient'
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post('/register', json={
            'email': 'newuser@example.com',
            'password': 'securepass123'
        })
        assert response.status_code == 400
        assert 'Missing required fields' in response.json['message']
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post('/register', json={
            'email': 'invalid-email',
            'password': 'securepass123',
            'full_name': 'Test User'
        })
        assert response.status_code == 400
        assert 'Invalid email format' in response.json['message']
    
    def test_register_short_password(self, client):
        """Test registration with password less than 8 characters."""
        response = client.post('/register', json={
            'email': 'newuser@example.com',
            'password': 'short',
            'full_name': 'Test User'
        })
        assert response.status_code == 400
        assert 'Password must be at least 8 characters' in response.json['message']
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with email that already exists."""
        response = client.post('/register', json={
            'email': 'testuser@example.com',
            'password': 'securepass123',
            'full_name': 'Another User'
        })
        assert response.status_code == 409
        assert 'Email already registered' in response.json['message']
    
    def test_register_invalid_role(self, client):
        """Test registration with invalid role."""
        response = client.post('/register', json={
            'email': 'newuser@example.com',
            'password': 'securepass123',
            'full_name': 'Test User',
            'role': 'superuser'
        })
        assert response.status_code == 400
        assert 'Unsupported role' in response.json['message']
    
    def test_register_doctor_role(self, client):
        """Test registration with doctor role."""
        response = client.post('/register', json={
            'email': 'newdoctor@example.com',
            'password': 'securepass123',
            'full_name': 'Dr. New',
            'role': 'doctor',
            'specialization': 'Neurology'
        })
        assert response.status_code == 201
        assert response.json['user']['role'] == 'doctor'
        assert response.json['user']['specialization'] == 'Neurology'
    
    def test_register_invalid_json(self, client):
        """Test registration with invalid JSON."""
        response = client.post('/register', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400


class TestUserLogin:
    """Test user login endpoint."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/login', json={
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json
        assert response.json['user']['email'] == 'testuser@example.com'
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post('/login', json={
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['message']
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', json={
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        })
        assert response.status_code == 401
        assert 'Invalid credentials' in response.json['message']
    
    def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = client.post('/login', json={
            'email': 'testuser@example.com'
        })
        assert response.status_code == 400
        assert 'Missing credentials' in response.json['message']
    
    def test_login_inactive_account(self, client):
        """Test login with inactive account."""
        with app.app_context():
            user = User.query.filter_by(email='testuser@example.com').first()
            user.is_active = False
            db.session.commit()
        
        response = client.post('/login', json={
            'email': 'testuser@example.com',
            'password': 'testpassword123'
        })
        assert response.status_code == 403
        assert 'Account is inactive' in response.json['message']
    
    def test_login_invalid_json(self, client):
        """Test login with invalid JSON."""
        response = client.post('/login', 
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400


class TestUserProfile:
    """Test user profile endpoints."""
    
    def test_get_profile_success(self, client, auth_token):
        """Test getting user profile."""
        response = client.get('/users/profile', 
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 200
        assert response.json['email'] == 'testuser@example.com'
        assert response.json['full_name'] == 'Test User'
    
    def test_get_profile_without_token(self, client):
        """Test getting profile without authentication."""
        response = client.get('/users/profile')
        assert response.status_code == 401
    
    def test_get_profile_by_id_same_user(self, client, auth_token, test_user):
        """Test getting profile by ID for same user."""
        response = client.get(f'/profile/{test_user.id}',
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 200
        assert response.json['email'] == 'testuser@example.com'
    
    def test_get_profile_by_id_patient_access_denied(self, client, auth_token, test_doctor):
        """Test patient cannot access other user's profile."""
        response = client.get(f'/profile/{test_doctor.id}',
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 403
        assert 'Access forbidden' in response.json['message']
    
    def test_get_profile_by_id_doctor_access_allowed(self, client, doctor_auth_token, test_user):
        """Test doctor can access patient profile."""
        response = client.get(f'/profile/{test_user.id}',
                             headers={'Authorization': f'Bearer {doctor_auth_token}'})
        assert response.status_code == 200
        assert response.json['email'] == 'testuser@example.com'
    
    def test_get_profile_by_id_admin_access_allowed(self, client, admin_auth_token, test_user):
        """Test admin can access any user profile."""
        response = client.get(f'/profile/{test_user.id}',
                             headers={'Authorization': f'Bearer {admin_auth_token}'})
        assert response.status_code == 200
        assert response.json['email'] == 'testuser@example.com'
    
    def test_get_profile_by_id_nonexistent(self, client, auth_token):
        """Test getting non-existent user profile."""
        response = client.get('/profile/99999',
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 404
        assert 'User not found' in response.json['message']
    
    def test_update_profile_success(self, client, auth_token):
        """Test updating user profile."""
        response = client.put('/users/profile',
                             json={
                                 'full_name': 'Updated Name',
                                 'phone': '9876543210'
                             },
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 200
        assert response.json['user']['full_name'] == 'Updated Name'
        assert response.json['user']['phone'] == '9876543210'
    
    def test_update_profile_without_token(self, client):
        """Test updating profile without authentication."""
        response = client.put('/users/profile',
                             json={'full_name': 'New Name'})
        assert response.status_code == 401
    
    def test_update_profile_invalid_json(self, client, auth_token):
        """Test updating profile with invalid JSON."""
        response = client.put('/users/profile',
                             data='invalid json',
                             content_type='application/json',
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 400


class TestDoctorListing:
    """Test doctor listing endpoints."""
    
    def test_list_doctors_success(self, client, test_doctor):
        """Test listing all doctors."""
        response = client.get('/doctors')
        assert response.status_code == 200
        assert response.json['total'] >= 1
        assert any(doc['email'] == 'doctor@example.com' for doc in response.json['doctors'])
    
    def test_list_doctors_empty(self, client):
        """Test listing doctors when none exist."""
        response = client.get('/doctors')
        assert response.status_code == 200
        assert response.json['total'] == 0
        assert response.json['doctors'] == []
    
    def test_get_doctor_success(self, client, test_doctor):
        """Test getting specific doctor."""
        response = client.get(f'/doctors/{test_doctor.id}')
        assert response.status_code == 200
        assert response.json['email'] == 'doctor@example.com'
        assert response.json['role'] == 'doctor'
        assert response.json['specialization'] == 'Cardiology'
    
    def test_get_doctor_nonexistent(self, client):
        """Test getting non-existent doctor."""
        response = client.get('/doctors/99999')
        assert response.status_code == 404
        assert 'Doctor not found' in response.json['message']
    
    def test_get_doctor_patient_not_doctor(self, client, test_user):
        """Test that getting doctor endpoint returns 404 for non-doctors."""
        response = client.get(f'/doctors/{test_user.id}')
        assert response.status_code == 404
        assert 'Doctor not found' in response.json['message']


class TestUserAccess:
    """Test user access endpoints (role-restricted)."""
    
    def test_get_user_admin_access(self, client, admin_auth_token, test_user):
        """Test admin can access user endpoint."""
        response = client.get(f'/users/{test_user.id}',
                             headers={'Authorization': f'Bearer {admin_auth_token}'})
        assert response.status_code == 200
        assert response.json['email'] == 'testuser@example.com'
    
    def test_get_user_doctor_access(self, client, doctor_auth_token, test_user):
        """Test doctor can access user endpoint."""
        response = client.get(f'/users/{test_user.id}',
                             headers={'Authorization': f'Bearer {doctor_auth_token}'})
        assert response.status_code == 200
        assert response.json['email'] == 'testuser@example.com'
    
    def test_get_user_patient_denied(self, client, auth_token):
        """Test patient cannot access user endpoint."""
        # Try to access with another user's ID
        with app.app_context():
            other_user = User(
                email='other@example.com',
                full_name='Other User',
                role='patient'
            )
            other_user.set_password('pass123')
            db.session.add(other_user)
            db.session.commit()
            other_id = other_user.id
        
        response = client.get(f'/users/{other_id}',
                             headers={'Authorization': f'Bearer {auth_token}'})
        assert response.status_code == 403
        assert 'Access forbidden' in response.json['message']
    
    def test_get_user_without_token(self, client, test_user):
        """Test accessing user endpoint without token."""
        response = client.get(f'/users/{test_user.id}')
        assert response.status_code == 401


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        assert 'healthy' in response.json['status'].lower()


class TestUserModel:
    """Test User model methods."""
    
    def test_set_password(self):
        """Test password hashing."""
        user = User(email='test@example.com', full_name='Test')
        user.set_password('mypassword')
        assert user.password_hash != 'mypassword'
        assert user.check_password('mypassword')
    
    def test_check_password_wrong(self):
        """Test password check with wrong password."""
        user = User(email='test@example.com', full_name='Test')
        user.set_password('mypassword')
        assert not user.check_password('wrongpassword')
    
    def test_to_dict(self):
        """Test user to_dict method."""
        user = User(
            id=1,
            email='test@example.com',
            full_name='Test User',
            role='patient',
            phone='1234567890'
        )
        user_dict = user.to_dict()
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['full_name'] == 'Test User'
        assert user_dict['role'] == 'patient'
        assert user_dict['id'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
