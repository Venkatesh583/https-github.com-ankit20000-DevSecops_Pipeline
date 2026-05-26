from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import Config
from models import db, MedicalReport
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
jwt = JWTManager(app)

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

@app.route('/reports/upload', methods=['POST'])
@jwt_required()
def upload_report():
    current_user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400
    
    try:
        # Read file content
        file_content = file.read()
        file_size = len(file_content)
        
        # Generate S3 key
        s3_key = generate_s3_key(current_user_id, file.filename)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=app.config['AWS_S3_BUCKET'],
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
            Metadata={'patient_id': str(current_user_id)}
        )
        
        # Create database record
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
        
        return jsonify({
            'message': 'Report uploaded successfully',
            'report': report.to_dict()
        }), 201
    
    except ClientError as e:
        return jsonify({'message': f'S3 upload failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'message': f'Upload failed: {str(e)}'}), 500

@app.route('/reports/list', methods=['GET'])
@jwt_required()
def list_reports():
    current_user_id = get_jwt_identity()
    
    reports = MedicalReport.query.filter_by(patient_id=current_user_id).all()
    
    return jsonify({
        'total': len(reports),
        'reports': [r.to_dict() for r in reports]
    }), 200

@app.route('/reports/<int:report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    current_user_id = get_jwt_identity()
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if report.patient_id != current_user_id and not report.is_public:
        return jsonify({'message': 'Access forbidden'}), 403
    
    return jsonify(report.to_dict()), 200

@app.route('/reports/<int:report_id>/download', methods=['GET'])
@jwt_required()
def download_report(report_id):
    current_user_id = get_jwt_identity()
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'message': 'Report not found'}), 404
    
    if report.patient_id != current_user_id and not report.is_public:
        return jsonify({'message': 'Access forbidden'}), 403
    
    try:
        # Generate signed URL valid for 1 hour
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
    
    except ClientError as e:
        return jsonify({'message': f'Failed to generate download URL: {str(e)}'}), 500

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
        # Delete from S3
        s3_client.delete_object(
            Bucket=app.config['AWS_S3_BUCKET'],
            Key=report.file_key
        )
        
        # Delete from database
        db.session.delete(report)
        db.session.commit()
        
        return jsonify({'message': 'Report deleted successfully'}), 200
    
    except ClientError as e:
        return jsonify({'message': f'Failed to delete report: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'Report Service is healthy'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5003)
