"""
Shared pytest configuration and fixtures for all microservices.
"""

import pytest
import os
import sys
from pathlib import Path

# Add current directory to path to import services
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key-do-not-use-in-production',
        'SECRET_KEY': 'test-secret-key-do-not-use-in-production',
        'OTEL_SERVICE_NAME': 'test-service',
        'AWS_S3_BUCKET': 'test-bucket',
        'AWS_S3_REGION': 'us-east-1',
        'USER_SERVICE_URL': 'http://mock-user-service:5001'
    }


@pytest.fixture
def mock_jwt_claims():
    """Provide mock JWT claims for different user roles."""
    return {
        'patient': {
            'identity': 1,
            'claims': {'role': 'patient'}
        },
        'doctor': {
            'identity': 2,
            'claims': {'role': 'doctor'}
        },
        'admin': {
            'identity': 3,
            'claims': {'role': 'admin'}
        }
    }


@pytest.fixture
def mock_user_data():
    """Provide mock user data."""
    return {
        'patient': {
            'id': 1,
            'email': 'patient@example.com',
            'full_name': 'John Patient',
            'role': 'patient',
            'phone': '1234567890'
        },
        'doctor': {
            'id': 2,
            'email': 'doctor@example.com',
            'full_name': 'Dr. Smith',
            'role': 'doctor',
            'specialization': 'Cardiology',
            'phone': '0987654321'
        },
        'admin': {
            'id': 3,
            'email': 'admin@example.com',
            'full_name': 'Admin User',
            'role': 'admin',
            'phone': '5555555555'
        }
    }


@pytest.fixture
def mock_appointment_data():
    """Provide mock appointment data."""
    from datetime import datetime
    
    return {
        'valid': {
            'doctor_id': 2,
            'appointment_date': '2025-06-15',
            'time': '10:00 AM',
            'reason': 'Routine checkup'
        },
        'future': {
            'doctor_id': 2,
            'appointment_date': datetime(2025, 12, 15, 14, 0, 0),
            'time_slot': '02:00 PM',
            'status': 'pending'
        }
    }


@pytest.fixture
def mock_file_data():
    """Provide mock file data for upload tests."""
    import io
    
    return {
        'pdf': {
            'content': b'%PDF-1.4\n%fake pdf content',
            'filename': 'test_report.pdf',
            'mimetype': 'application/pdf'
        },
        'image': {
            'content': b'\xff\xd8\xff\xe0\n',  # JPEG magic bytes
            'filename': 'scan.jpg',
            'mimetype': 'image/jpeg'
        },
        'invalid': {
            'content': b'malware code here',
            'filename': 'malware.exe',
            'mimetype': 'application/x-msdownload'
        }
    }


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        'markers', 'unit: mark test as a unit test'
    )
    config.addinivalue_line(
        'markers', 'integration: mark test as an integration test'
    )
    config.addinivalue_line(
        'markers', 'slow: mark test as slow running'
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected items during the collection phase."""
    for item in items:
        # Add markers based on test file location
        if 'test_app.py' in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif 'test_integration.py' in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def reset_mock_calls(monkeypatch):
    """Reset mock calls after each test."""
    yield
    # Cleanup happens automatically with function scope


@pytest.fixture
def disable_observability(monkeypatch):
    """Disable OpenTelemetry instrumentation for tests."""
    monkeypatch.setenv('OTEL_SDK_DISABLED', 'true')
    yield


@pytest.fixture
def disable_s3(monkeypatch):
    """Mock S3 client to prevent real AWS calls."""
    from unittest.mock import MagicMock, patch
    
    mock_s3 = MagicMock()
    with patch('app.s3_client', mock_s3):
        yield mock_s3


@pytest.fixture
def disable_requests(monkeypatch):
    """Mock requests library to prevent real HTTP calls."""
    from unittest.mock import MagicMock, patch
    
    mock_requests = MagicMock()
    with patch('app.requests', mock_requests):
        yield mock_requests


@pytest.fixture
def test_database_url():
    """Provide test database URL."""
    return 'sqlite:///:memory:'


@pytest.fixture
def suppress_logging():
    """Suppress verbose logging during tests."""
    import logging
    
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


# Markers for test categorization
def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        '--slow', action='store_true', default=False,
        help='run slow tests'
    )
    parser.addoption(
        '--integration', action='store_true', default=False,
        help='run integration tests'
    )


def pytest_runtest_setup(item):
    """Setup for each test."""
    # Skip slow tests unless --slow is specified
    if 'slow' in item.keywords and not item.config.getoption('--slow'):
        pytest.skip('need --slow option to run')
    
    # Skip integration tests unless --integration is specified
    if 'integration' in item.keywords and not item.config.getoption('--integration'):
        pytest.skip('need --integration option to run')
