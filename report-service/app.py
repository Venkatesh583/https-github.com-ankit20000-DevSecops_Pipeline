import logging
import os

import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from flask import Flask, g, jsonify, request
from flask_jwt_extended import JWTManager, get_jwt, get_jwt_identity, jwt_required

from config import Config
from models import MedicalReport, db
from observability import configure_observability, log_event

app = Flask(__name__)
app.config.from_object(Config)
app.config['SERVICE_NAME'] = os.getenv('OTEL_SERVICE_NAME', 'report-service')

db.init_app(app)
jwt = JWTManager(app)
configure_observability(app, app.config['SERVICE_NAME'])

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['AWS_S3_REGION']
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_s3_key(patient_id, filename):
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"reports/patient_{patient_id}/{timestamp}_{filename}"


def get_current_user():
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    return current_user_id, jwt_data.get('role')


@app.route('/reports/upload', methods=['POST'])
@jwt_required()
def upload_report():
    current_user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({'error': 'validation_error', 'message': 'No file provided', 'request_id': getattr(g, 'request_id', None)}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'validation_error', 'message': 'No file selected', 'request_id': getattr(g, 'request_id', None)}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'validation_error', 'message': 'File type not allowed', 'request_id': getattr(g, 'request_id', None)}), 400

    try:
        file_content = file.read()
        file_size = len(file_content)
        s3_key = generate_s3_key(current_user_id, file.filename)

        log_event(logging.INFO, 's3_upload_started', request_id=getattr(g, 'request_id', None), patient_id=current_user_id, s3_key=s3_key, file_name=file.filename)

        s3_client.put_object(
            Bucket=app.config['AWS_S3_BUCKET'],
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
            Metadata={'patient_id': str(current_user_id)}
        )

        report = MedicalReport(
            patient_id=current_user_id,
            file_name=file.filename,
            file_key=s3_key,
            file_size=file_size,
            file_type=file.filename.rsplit('.', 1)[1].lower(),
            description=request.form.get('description', ''),
            is_public=request.form.get('is_public', 'false').lower() == 'true'
        )

        db.session.add(report)
        db.session.commit()

        log_event(logging.INFO, 'report_uploaded', request_id=getattr(g, 'request_id', None), report_id=report.id, patient_id=current_user_id, s3_key=s3_key)

        return jsonify({
            'message': 'Report uploaded successfully',
            'report': report.to_dict()
        }), 201

    except ClientError as exc:
        log_event(logging.ERROR, 's3_upload_failed', request_id=getattr(g, 'request_id', None), patient_id=current_user_id, error=str(exc))
        return jsonify({'message': f'S3 upload failed: {str(exc)}'}), 500
    except Exception as exc:
        log_event(logging.ERROR, 'report_upload_failed', request_id=getattr(g, 'request_id', None), patient_id=current_user_id, error=str(exc))
        return jsonify({'message': f'Upload failed: {str(exc)}'}), 500

@app.route('/reports/list', methods=['GET'])
@jwt_required()
def list_reports():
    current_user_id = get_jwt_identity()
    
    reports = MedicalReport.query.filter_by(patient_id=current_user_id).all()
    
    return jsonify({
        'total': len(reports),
        'reports': [r.to_dict() for r in reports]
    }), 200

@app.route('/reports/patient/<int:patient_id>', methods=['GET'])
@jwt_required()
def list_reports_for_patient(patient_id):
    current_user_id, role = get_current_user()
    if current_user_id != patient_id and role != 'doctor':
        return jsonify({'message': 'Access forbidden'}), 403

    reports = MedicalReport.query.filter_by(patient_id=patient_id).all()
    return jsonify({
        'total': len(reports),
        'reports': [r.to_dict() for r in reports]
    }), 200

@app.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    current_user_id, role = get_current_user()
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if report.patient_id != current_user_id and role != 'doctor' and not report.is_public:
        return jsonify({'message': 'Access forbidden'}), 403
    
    return jsonify(report.to_dict()), 200

@app.route('/reports/<int:report_id>/download', methods=['GET'])
@jwt_required()
def download_report(report_id):
    current_user_id, role = get_current_user()
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if report.patient_id != current_user_id and role != 'doctor' and not report.is_public:
        return jsonify({'message': 'Access forbidden'}), 403
    
    try:
        log_event(logging.INFO, 'download_url_generated', request_id=getattr(g, 'request_id', None), report_id=report_id, patient_id=report.patient_id)
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': app.config['AWS_S3_BUCKET'],
                'Key': report.file_key
            },
            ExpiresIn=3600
        )
        
        return jsonify({
            'download_url': download_url,
            'expires_in_seconds': 3600
        }), 200
    
    except ClientError as exc:
        log_event(logging.ERROR, 'download_url_generation_failed', request_id=getattr(g, 'request_id', None), report_id=report_id, error=str(exc))
        return jsonify({'message': f'Failed to generate download URL: {str(exc)}'}), 500

@app.route('/reports/<int:report_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_report(report_id):
    current_user_id = get_jwt_identity()
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if report.patient_id != current_user_id:
        return jsonify({'message': 'Access forbidden'}), 403
    
    try:
        log_event(logging.INFO, 'report_delete_started', request_id=getattr(g, 'request_id', None), report_id=report_id, patient_id=current_user_id, s3_key=report.file_key)
        s3_client.delete_object(
            Bucket=app.config['AWS_S3_BUCKET'],
            Key=report.file_key
        )
        
        db.session.delete(report)
        db.session.commit()
        log_event(logging.INFO, 'report_deleted', request_id=getattr(g, 'request_id', None), report_id=report_id, patient_id=current_user_id)
        
        return jsonify({'message': 'Report deleted successfully'}), 200
    
    except ClientError as exc:
        log_event(logging.ERROR, 'report_delete_failed', request_id=getattr(g, 'request_id', None), report_id=report_id, error=str(exc))
        return jsonify({'message': f'Failed to delete report: {str(exc)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    log_event(logging.INFO, 'health_check', request_id=getattr(g, 'request_id', None), service=app.config['SERVICE_NAME'])
    return jsonify({'status': 'Report Service is healthy'}), 200


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
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=5003)
