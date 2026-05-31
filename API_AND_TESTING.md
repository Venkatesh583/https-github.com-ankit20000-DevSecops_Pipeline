# Healthcare Microservices - API Documentation & Testing Guide

## Overview

This document provides comprehensive API documentation and testing instructions for the healthcare microservices platform.

## Architecture Overview

The platform consists of 3 microservices:

```
┌─────────────────────────────────────────────────────────────┐
│                    Healthcare Microservices                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────┐  │
│  │ User Service     │  │ Appointment Svc  │  │ Report   │  │
│  │ (Port 5001)      │  │ (Port 5002)      │  │ Service  │  │
│  ├──────────────────┤  ├──────────────────┤  │(Port5003)│  │
│  │ • Register       │  │ • Book Appt      │  ├──────────┤  │
│  │ • Login          │  │ • List History   │  │ • Upload │  │
│  │ • Profiles       │  │ • Confirm Appt   │  │ • List   │  │
│  │ • Doctor List    │  │ • Cancel Appt    │  │ • Download
│  └──────────────────┘  └──────────────────┘  │ • Delete │  │
│           │                    │              └──────────┘  │
│           └────────────────────┴──────────────┘             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       PostgreSQL Database (Shared)                   │  │
│  │  • users  • appointments  • medical_reports          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │       AWS S3 (Medical Reports Storage)               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ OpenTelemetry Collector (Tracing & Metrics)          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## User Service API

### Base URL
`http://localhost:5001` or `http://user-service:5001` (Docker)

### Authentication
JWT-based authentication required for protected endpoints. Include token in Authorization header:
```
Authorization: Bearer <token>
```

### Endpoints

#### 1. User Registration
```http
POST /register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123",
  "full_name": "John Doe",
  "role": "patient",          // patient, doctor, or admin
  "phone": "1234567890",       // optional
  "specialization": "Cardiology" // optional, for doctors
}
```

**Responses:**
- `201`: User registered successfully
- `400`: Validation error (invalid email, short password, etc.)
- `409`: Email already registered

#### 2. User Login
```http
POST /login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123"
}
```

**Response (200):**
```json
{
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "patient"
  }
}
```

#### 3. Get User Profile
```http
GET /users/profile
Authorization: Bearer <token>
```

**Response (200):** User object with all fields

#### 4. Update User Profile
```http
PUT /users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
  "full_name": "Updated Name",
  "phone": "9876543210"
}
```

#### 5. List Doctors
```http
GET /doctors
```

**Response (200):**
```json
{
  "total": 5,
  "doctors": [
    {
      "id": 2,
      "email": "doctor@example.com",
      "full_name": "Dr. Smith",
      "role": "doctor",
      "specialization": "Cardiology"
    }
  ]
}
```

#### 6. Get Doctor Details
```http
GET /doctors/<doctor_id>
```

#### 7. Get User by ID (Admin/Doctor Only)
```http
GET /users/<user_id>
Authorization: Bearer <admin_or_doctor_token>
```

#### 8. Health Check
```http
GET /health
```

---

## Appointment Service API

### Base URL
`http://localhost:5002` or `http://appointment-service:5002` (Docker)

### Inter-Service Communication
Calls User Service at `USER_SERVICE_URL` environment variable.

### Endpoints

#### 1. List Doctors
```http
GET /doctors
```

Fetches doctors from User Service via REST API.

#### 2. Book Appointment
```http
POST /appointments
Authorization: Bearer <patient_token>
Content-Type: application/json

{
  "doctor_id": 2,
  "appointment_date": "2025-06-15",  // YYYY-MM-DD
  "time": "10:00 AM",                // HH:MM AM/PM
  "reason": "Routine checkup"
}
```

**Response (201):**
```json
{
  "message": "Appointment booked successfully",
  "appointment": {
    "id": 1,
    "patient_id": 1,
    "doctor_id": 2,
    "doctor_name": "Dr. Smith",
    "specialization": "Cardiology",
    "appointment_date": "2025-06-15T10:00:00",
    "time_slot": "10:00 AM",
    "status": "pending",
    "reason": "Routine checkup"
  }
}
```

**Error Responses:**
- `403`: Doctors cannot book appointments
- `404`: Doctor not found
- `409`: Appointment slot already booked

#### 3. Get Appointment History
```http
GET /appointments/history
Authorization: Bearer <token>
```

Returns different results based on user role:
- **Patient**: Their own appointments
- **Doctor**: Appointments with them as doctor

#### 4. Get Appointment by ID
```http
GET /appointments/<appointment_id>
Authorization: Bearer <token>
```

Only accessible by patient or doctor involved.

#### 5. Get Appointments by Patient
```http
GET /appointments/patient/<patient_id>
Authorization: Bearer <token>
```

Accessible by patient (self) or doctor.

#### 6. Cancel Appointment
```http
POST /appointments/<appointment_id>/cancel
Authorization: Bearer <patient_token>
```

Only patients can cancel their appointments.

#### 7. Confirm Appointment
```http
POST /appointments/<appointment_id>/confirm
Authorization: Bearer <doctor_token>
Content-Type: application/json

{
  "notes": "Patient confirmed for appointment"  // optional
}
```

Only doctors can confirm appointments.

#### 8. Delete Appointment
```http
DELETE /appointments/<appointment_id>
Authorization: Bearer <token>
```

Accessible by patient, doctor, or admin.

#### 9. Health Check
```http
GET /health
```

---

## Report Service API

### Base URL
`http://localhost:5003` or `http://report-service:5003` (Docker)

### Storage
Medical reports are stored in AWS S3 bucket.

### Endpoints

#### 1. Upload Report
```http
POST /reports/upload
Authorization: Bearer <patient_token>
Content-Type: multipart/form-data

file: <file>  // PDF, PNG, JPG, DOC, DOCX (max 50MB)
description: "Medical report description"  // optional
is_public: "false"  // optional, "true" or "false"
```

**Response (201):**
```json
{
  "message": "Report uploaded successfully",
  "report": {
    "id": 1,
    "patient_id": 1,
    "file_name": "test_report.pdf",
    "file_type": "pdf",
    "file_size": 1024,
    "description": "Medical report",
    "is_public": false,
    "created_at": "2025-06-15T10:00:00Z"
  }
}
```

#### 2. List Reports
```http
GET /reports/list
Authorization: Bearer <patient_token>
```

Returns reports for authenticated user.

#### 3. Get Reports for Patient
```http
GET /reports/patient/<patient_id>
Authorization: Bearer <doctor_or_patient_token>
```

Accessible by patient (self) or doctor.

#### 4. Get Report Details
```http
GET /reports/<report_id>
Authorization: Bearer <token>
```

Accessible by report owner, doctor, or if public.

#### 5. Download Report
```http
GET /reports/<report_id>/download
Authorization: Bearer <token>
```

Returns presigned S3 URL valid for 1 hour:
```json
{
  "download_url": "https://s3.amazonaws.com/...",
  "expires_in_seconds": 3600
}
```

#### 6. Delete Report
```http
DELETE /reports/<report_id>/delete
Authorization: Bearer <patient_token>
```

Only report owner can delete.

#### 7. Health Check
```http
GET /health
```

---

## Testing Instructions

### 1. Install Test Dependencies

```bash
cd user-service
pip install -r requirements.txt

cd ../appointment-service
pip install -r requirements.txt

cd ../report-service
pip install -r requirements.txt
```

Dependencies include:
- `pytest` - Testing framework
- `pytest-cov` - Code coverage
- `pytest-mock` - Mocking support
- `responses` - HTTP request mocking
- `moto` - AWS service mocking

### 2. Run Unit Tests

#### User Service Tests
```bash
cd user-service
pytest test_app.py -v              # Run all tests
pytest test_app.py -v --cov        # With coverage report
pytest test_app.py::TestUserRegistration -v  # Run specific class
```

Test Classes:
- `TestUserRegistration` - Registration validation
- `TestUserLogin` - Login authentication
- `TestUserProfile` - Profile management
- `TestDoctorListing` - Doctor endpoints
- `TestUserAccess` - Role-based access
- `TestHealthCheck` - Service health
- `TestUserModel` - Model methods

#### Appointment Service Tests
```bash
cd appointment-service
pytest test_app.py -v
pytest test_app.py -v --cov
```

Test Classes:
- `TestAppointmentBooking` - Appointment creation
- `TestAppointmentHistory` - History retrieval
- `TestAppointmentCancellation` - Cancellation logic
- `TestAppointmentConfirmation` - Doctor confirmation
- `TestAppointmentAccess` - Access control
- `TestAppointmentModel` - Model methods
- `TestInterServiceCommunication` - User service calls
- `TestHealthCheck` - Service health

#### Report Service Tests
```bash
cd report-service
pytest test_app.py -v
pytest test_app.py -v --cov
```

Test Classes:
- `TestFileValidation` - File type validation
- `TestS3KeyGeneration` - S3 key format
- `TestReportUpload` - Upload functionality
- `TestReportListing` - Report retrieval
- `TestReportRetrieval` - Access control
- `TestReportDownload` - Download URLs
- `TestReportDeletion` - Deletion logic
- `TestMedicalReportModel` - Model methods
- `TestAccessControl` - Role-based access

### 3. Run Integration Tests

```bash
cd ..  # Back to root directory
pytest test_integration.py -v
```

Integration Tests Cover:
- API endpoint existence
- Inter-service communication
- Authentication mechanisms
- Error handling
- Access control
- Data validation
- Logging
- OpenTelemetry instrumentation

### 4. Run All Tests with Coverage

```bash
# Run all tests with coverage report
pytest -v --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 5. Docker-Based Testing

```bash
# Start services
docker-compose up -d

# Install test dependencies in container
docker exec appointment-service pip install pytest pytest-cov

# Run tests in container
docker exec appointment-service pytest test_app.py -v

# View logs
docker-compose logs -f appointment-service
```

---

## OpenTelemetry Instrumentation

All services are instrumented with OpenTelemetry for tracing and metrics collection.

### Configured Instrumentation

1. **Flask Instrumentation**
   - Traces HTTP requests
   - Records request/response details

2. **Requests Instrumentation**
   - Traces inter-service HTTP calls
   - Records remote service latency

3. **SQLAlchemy Instrumentation**
   - Traces database queries
   - Records query performance

### Structured JSON Logging

All services output structured JSON logs with:
- Timestamp (ISO 8601)
- Service name
- Log level
- Request ID for correlation
- Trace ID and Span ID
- Custom fields (status code, duration, error, etc.)

Example Log Entry:
```json
{
  "timestamp": "2025-06-15T10:00:00.000Z",
  "service": "appointment-service",
  "level": "INFO",
  "message": "appointment_booked",
  "request_id": "req-12345",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "appointment_id": 1,
  "patient_id": 1,
  "doctor_id": 2,
  "duration_ms": 45.32
}
```

### OTLP Exporter Configuration

```yaml
# otel-collector-config.yaml
exporters:
  otlp:
    protocols:
      http:
        endpoint: http://localhost:4318
```

---

## Environment Variables

Create a `.env` file in project root:

```bash
# JWT Configuration
JWT_SECRET_KEY=your_secret_key_here
SECRET_KEY=your_secret_key_here

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/healthcare_db

# Services (for Docker Compose)
USER_SERVICE_URL=http://user-service:5001
APPOINTMENT_SERVICE_URL=http://appointment-service:5002
REPORT_SERVICE_URL=http://report-service:5003

# AWS S3
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_s3_bucket_name
AWS_S3_REGION=us-east-1

# OpenTelemetry
OTEL_SERVICE_NAME=service-name
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

---

## Error Codes

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing/invalid JWT token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 500 | Internal Error | Server error |

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "request_id": "req-12345"
}
```

---

## Testing Best Practices

1. **Unit Tests**: Test individual functions and endpoints
2. **Integration Tests**: Test service interactions
3. **Mocking**: Mock external services (S3, user-service)
4. **Fixtures**: Use pytest fixtures for test data
5. **Coverage**: Aim for >80% code coverage
6. **Isolation**: Each test should be independent
7. **Clear Names**: Test names should describe what they test

---

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Ensure PostgreSQL is running
   psql -U postgres -d healthcare_db
   ```

2. **JWT Token Invalid**
   - Ensure `JWT_SECRET_KEY` is consistent across services
   - Token should be passed in Authorization header

3. **Inter-Service Communication Fails**
   - Check `USER_SERVICE_URL` is correct
   - Ensure services are running
   - Check firewall/network policies

4. **S3 Upload Fails**
   - Verify AWS credentials
   - Check S3 bucket exists
   - Verify IAM permissions

---

## Next Steps

1. Deploy microservices using Docker Compose or Kubernetes
2. Set up monitoring with ELK stack or Datadog
3. Implement CI/CD pipeline with GitHub Actions
4. Add database migrations with Alembic
5. Implement caching with Redis
6. Add API rate limiting
7. Implement comprehensive logging aggregation

