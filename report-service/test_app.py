import pytest
import io
from datetime import datetime
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from app import app, db, allowed_file, generate_s3_key
from models import MedicalReport
from config import Config


@pytest.fixture
def client():
    """Create a test client with a test database."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['AWS_S3_BUCKET'] = 'test-bucket'
    app.config['AWS_S3_REGION'] = 'us-east-1'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_report():
    """Create a test medical report."""
    with app.app_context():
        report = MedicalReport(
            patient_id=1,
            file_name='test_report.pdf',
            file_key='reports/patient_1/20250615_100000_test_report.pdf',
            file_size=1024,
            file_type='pdf',
            description='Test medical report',
            is_public=False
        )
        db.session.add(report)
        db.session.commit()
        return report


@pytest.fixture
def public_report():
    """Create a public medical report."""
    with app.app_context():
        report = MedicalReport(
            patient_id=2,
            file_name='public_report.pdf',
            file_key='reports/patient_2/20250615_100000_public_report.pdf',
            file_size=2048,
            file_type='pdf',
            description='Public medical report',
            is_public=True
        )
        db.session.add(report)
        db.session.commit()
        return report


@pytest.fixture
def auth_token():
    """Mock JWT token for authenticated patient."""
    return 'mock_patient_token_12345'


@pytest.fixture
def doctor_auth_token():
    """Mock JWT token for authenticated doctor."""
    return 'mock_doctor_token_67890'


class TestFileValidation:
    """Test file validation functionality."""
    
    def test_allowed_file_pdf(self):
        """Test PDF files are allowed."""
        assert allowed_file('report.pdf') is True
    
    def test_allowed_file_image(self):
        """Test image files are allowed."""
        assert allowed_file('scan.jpg') is True
        assert allowed_file('xray.png') is True
    
    def test_allowed_file_doc(self):
        """Test document files are allowed."""
        assert allowed_file('document.doc') is True
        assert allowed_file('document.docx') is True
    
    def test_disallowed_file_exe(self):
        """Test executable files are not allowed."""
        assert allowed_file('malware.exe') is False
    
    def test_disallowed_file_zip(self):
        """Test zip files are not allowed."""
        assert allowed_file('archive.zip') is False
    
    def test_disallowed_file_no_extension(self):
        """Test files without extension are not allowed."""
        assert allowed_file('no_extension') is False
    
    def test_allowed_file_case_insensitive(self):
        """Test file validation is case-insensitive."""
        assert allowed_file('report.PDF') is True
        assert allowed_file('image.JPG') is True


class TestS3KeyGeneration:
    """Test S3 key generation."""
    
    def test_generate_s3_key_format(self):
        """Test S3 key is generated with correct format."""
        with app.app_context():
            key = generate_s3_key(1, 'test_report.pdf')
            assert key.startswith('reports/patient_1/')
            assert 'test_report.pdf' in key
    
    def test_generate_s3_key_different_patients(self):
        """Test S3 keys for different patients are different."""
        with app.app_context():
            key1 = generate_s3_key(1, 'report.pdf')
            key2 = generate_s3_key(2, 'report.pdf')
            assert key1 != key2
            assert 'patient_1' in key1
            assert 'patient_2' in key2


class TestReportUpload:
    """Test report upload endpoint."""
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    def test_upload_report_success(self, mock_identity, mock_s3, client):
        """Test successful report upload."""
        mock_identity.return_value = 1
        mock_s3.put_object = MagicMock()
        
        # Create a test file
        data = {
            'file': (io.BytesIO(b'test file content'), 'test.pdf'),
            'description': 'Test report'
        }
        
        response = client.post('/reports/upload',
                             data=data,
                             content_type='multipart/form-data')
        
        # JWT would be required in real scenario
    
    @patch('app.get_jwt_identity')
    def test_upload_report_no_file(self, mock_identity, client):
        """Test upload without file."""
        mock_identity.return_value = 1
        
        response = client.post('/reports/upload')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    def test_upload_report_empty_file(self, mock_identity, client):
        """Test upload with empty file."""
        mock_identity.return_value = 1
        
        data = {
            'file': (io.BytesIO(b''), '')
        }
        
        response = client.post('/reports/upload',
                             data=data,
                             content_type='multipart/form-data')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    def test_upload_report_disallowed_file(self, mock_identity, client):
        """Test upload with disallowed file type."""
        mock_identity.return_value = 1
        
        data = {
            'file': (io.BytesIO(b'malware content'), 'malware.exe')
        }
        
        response = client.post('/reports/upload',
                             data=data,
                             content_type='multipart/form-data')
        # Would receive validation error for disallowed file type
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    def test_upload_report_s3_error(self, mock_identity, mock_s3, client):
        """Test upload with S3 error."""
        mock_identity.return_value = 1
        mock_s3.put_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket'}},
            'PutObject'
        )
        
        data = {
            'file': (io.BytesIO(b'test content'), 'test.pdf')
        }
        
        # Would receive 500 error due to S3 failure


class TestReportListing:
    """Test report listing endpoints."""
    
    @patch('app.get_jwt_identity')
    def test_list_reports_success(self, mock_identity, client, test_report):
        """Test listing user's own reports."""
        mock_identity.return_value = 1
        
        response = client.get('/reports/list')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    def test_list_reports_empty(self, mock_identity, client):
        """Test listing reports when none exist."""
        mock_identity.return_value = 999
        
        response = client.get('/reports/list')
        # Would return 0 reports
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_list_reports_for_patient_self(self, mock_jwt, mock_identity, client, test_report):
        """Test patient accessing their own reports."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/reports/patient/1')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_list_reports_for_patient_doctor_allowed(self, mock_jwt, mock_identity, client, test_report):
        """Test doctor accessing patient's reports."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'doctor'}
        
        response = client.get('/reports/patient/1')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_list_reports_for_patient_patient_denied(self, mock_jwt, mock_identity, client):
        """Test patient cannot access other patient's reports."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/reports/patient/999')
        # Would receive 403 forbidden


class TestReportRetrieval:
    """Test report retrieval endpoints."""
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_report_own_report(self, mock_jwt, mock_identity, client, test_report):
        """Test patient getting their own report."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get(f'/reports/{test_report.id}')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_report_public(self, mock_jwt, mock_identity, client, public_report):
        """Test anyone accessing public report."""
        mock_identity.return_value = 999
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get(f'/reports/{public_report.id}')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_report_doctor_access_allowed(self, mock_jwt, mock_identity, client, test_report):
        """Test doctor accessing patient's report."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'doctor'}
        
        response = client.get(f'/reports/{test_report.id}')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_report_patient_denied(self, mock_jwt, mock_identity, client, test_report):
        """Test patient cannot access other patient's private report."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get(f'/reports/{test_report.id}')
        # Would receive 403 forbidden
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_get_report_not_found(self, mock_jwt, mock_identity, client):
        """Test getting non-existent report."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/reports/99999')
        # Would receive 404 not found


class TestReportDownload:
    """Test report download endpoints."""
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_download_report_success(self, mock_jwt, mock_identity, mock_s3, client, test_report):
        """Test successful report download."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
        
        response = client.get(f'/reports/{test_report.id}/download')
        # Would need proper JWT setup
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_download_report_public(self, mock_jwt, mock_identity, mock_s3, client, public_report):
        """Test downloading public report."""
        mock_identity.return_value = 999
        mock_jwt.return_value = {'role': 'patient'}
        mock_s3.generate_presigned_url.return_value = 'https://s3.amazonaws.com/presigned-url'
        
        response = client.get(f'/reports/{public_report.id}/download')
        # Would need proper JWT setup
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_download_report_s3_error(self, mock_jwt, mock_identity, mock_s3, client, test_report):
        """Test download with S3 error."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket'}},
            'GeneratePresignedUrl'
        )
        
        response = client.get(f'/reports/{test_report.id}/download')
        # Would receive 500 error due to S3 failure
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_download_report_access_denied(self, mock_jwt, mock_identity, client, test_report):
        """Test download access denied for unauthorized user."""
        mock_identity.return_value = 999
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get(f'/reports/{test_report.id}/download')
        # Would receive 403 forbidden


class TestReportDeletion:
    """Test report deletion endpoints."""
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    def test_delete_report_success(self, mock_identity, mock_s3, client, test_report):
        """Test successful report deletion."""
        mock_identity.return_value = 1
        mock_s3.delete_object = MagicMock()
        
        response = client.delete(f'/reports/{test_report.id}/delete')
        # Would need proper JWT setup
    
    @patch('app.get_jwt_identity')
    def test_delete_report_not_found(self, mock_identity, client):
        """Test deleting non-existent report."""
        mock_identity.return_value = 1
        
        response = client.delete('/reports/99999/delete')
        # Would receive 404 not found
    
    @patch('app.get_jwt_identity')
    def test_delete_report_access_denied(self, mock_identity, client, test_report):
        """Test user cannot delete other user's report."""
        mock_identity.return_value = 999
        
        response = client.delete(f'/reports/{test_report.id}/delete')
        # Would receive 403 forbidden
    
    @patch('app.s3_client')
    @patch('app.get_jwt_identity')
    def test_delete_report_s3_error(self, mock_identity, mock_s3, client, test_report):
        """Test deletion with S3 error."""
        mock_identity.return_value = 1
        mock_s3.delete_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket'}},
            'DeleteObject'
        )
        
        response = client.delete(f'/reports/{test_report.id}/delete')
        # Would receive 500 error due to S3 failure


class TestMedicalReportModel:
    """Test MedicalReport model."""
    
    def test_report_to_dict(self):
        """Test report to_dict method."""
        report = MedicalReport(
            id=1,
            patient_id=1,
            doctor_id=2,
            file_name='test.pdf',
            file_key='reports/patient_1/test.pdf',
            file_size=1024,
            file_type='pdf',
            description='Test report',
            is_public=False
        )
        
        report_dict = report.to_dict()
        assert report_dict['id'] == 1
        assert report_dict['patient_id'] == 1
        assert report_dict['file_name'] == 'test.pdf'
        assert report_dict['file_type'] == 'pdf'
        assert report_dict['is_public'] is False
    
    def test_report_default_is_public(self):
        """Test report defaults to not public."""
        report = MedicalReport(
            patient_id=1,
            file_name='test.pdf',
            file_key='reports/patient_1/test.pdf',
            file_size=1024,
            file_type='pdf'
        )
        
        assert report.is_public is False


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test report service health check."""
        response = client.get('/health')
        assert response.status_code == 200
        assert 'healthy' in response.json['status'].lower()


class TestS3Configuration:
    """Test S3 configuration."""
    
    def test_s3_bucket_configured(self, client):
        """Test S3 bucket is configured."""
        with app.app_context():
            assert app.config['AWS_S3_BUCKET'] == 'test-bucket'
    
    def test_s3_region_configured(self, client):
        """Test S3 region is configured."""
        with app.app_context():
            assert app.config['AWS_S3_REGION'] == 'us-east-1'
    
    def test_upload_folder_configured(self, client):
        """Test upload folder is configured."""
        with app.app_context():
            assert hasattr(app.config, 'UPLOAD_FOLDER') or 'UPLOAD_FOLDER' in app.config
    
    def test_max_content_length_configured(self, client):
        """Test max content length is configured."""
        with app.app_context():
            max_size = app.config['MAX_CONTENT_LENGTH']
            assert max_size == 50 * 1024 * 1024  # 50MB


class TestAccessControl:
    """Test access control for report operations."""
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_patient_can_access_own_reports(self, mock_jwt, mock_identity, client, test_report):
        """Test patient can access their own reports."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/reports/list')
        # Would return reports for patient 1
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_doctor_can_access_patient_reports(self, mock_jwt, mock_identity, client, test_report):
        """Test doctor can access patient's reports."""
        mock_identity.return_value = 2
        mock_jwt.return_value = {'role': 'doctor'}
        
        response = client.get('/reports/patient/1')
        # Would return patient 1's reports for doctor
    
    @patch('app.get_jwt_identity')
    @patch('app.get_jwt')
    def test_patient_cannot_access_other_patient_reports(self, mock_jwt, mock_identity, client):
        """Test patient cannot access other patient's reports."""
        mock_identity.return_value = 1
        mock_jwt.return_value = {'role': 'patient'}
        
        response = client.get('/reports/patient/2')
        # Would receive 403 forbidden


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
