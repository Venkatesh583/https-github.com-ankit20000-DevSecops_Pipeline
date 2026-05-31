# Healthcare Microservices Platform

A comprehensive healthcare platform built with Flask microservices, PostgreSQL, and AWS S3.

## Architecture

### 1. **Patient Service / User Service** (Port 5001)
- Patient registration and authentication
- JWT-based authentication
- User profile management
- Doctor profile listing

**Endpoints:**
- `POST /register` - Register new user
- `POST /login` - User login with JWT
- `GET /users/profile` - Get your user profile
- `PUT /users/profile` - Update your user profile
- `GET /profile/<id>` - Get profile by user ID (self, doctor, admin)
- `GET /doctors` - List doctors
- `GET /doctors/<id>` - Get doctor details
- `GET /health` - Health check

### 2. **Doctor Appointment Service** (Port 5002)
- List doctors
- Book appointments with doctors
- View appointment history
- Cancel appointments
- Confirm appointments (Doctor)
- Prevent double bookings

**Endpoints:**
- `GET /doctors` - List available doctors
- `POST /appointments` - Book appointment
- `POST /appointments/book` - Book appointment alias
- `GET /appointments/history` - View your appointment history
- `GET /appointments/patient/<patientId>` - View appointments for a patient (doctor access)
- `GET /appointments/<id>` - Get appointment details
- `DELETE /appointments/<id>` - Cancel appointment
- `POST /appointments/<id>/cancel` - Cancel appointment alias
- `POST /appointments/<id>/confirm` - Confirm appointment (Doctor)
- `GET /health` - Health check

### 3. **Medical Report Service** (Port 5003)
- Upload medical reports to AWS S3
- List patient reports
- Download reports with signed URLs
- Delete reports
- Doctor access to patient reports

**Endpoints:**
- `POST /reports/upload` - Upload medical report
- `GET /reports/list` - List your reports
- `GET /reports/patient/<patientId>` - List a patient's reports (doctor access)
- `GET /reports/<id>` - Get report details
- `GET /reports/<id>/download` - Download report (signed URL)
- `DELETE /reports/<id>` - Delete report
- `GET /health` - Health check

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- AWS S3 bucket
- Docker & Docker Compose (optional)

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/ankit20000/DevSecops_Pipeline.git
cd healthcare-microservices
```

### 2. Create `.env` file
Copy `.env.example` and update with your credentials:
```bash
cp .env.example .env
```

### 3. Install Dependencies
```bash
# User Service
cd user-service
pip install -r requirements.txt

# Appointment Service
cd ../appointment-service
pip install -r requirements.txt

# Report Service
cd ../report-service
pip install -r requirements.txt
```

### 4. Initialize Database
```bash
# Create PostgreSQL database
createdb healthcare_db

# Run migrations (each service creates tables on startup)
```

### 5. Run Services

#### Option A: Run Individually
```bash
# Terminal 1: User Service
cd user-service
python app.py

# Terminal 2: Appointment Service
cd appointment-service
python app.py

# Terminal 3: Report Service
cd report-service
python app.py
```

#### Option B: Run with Docker Compose
```bash
docker-compose up -d
```

## Environment Variables

See `.env.example` for all required environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/healthcare_db

# JWT
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_S3_BUCKET=your-s3-bucket
AWS_S3_REGION=us-east-1

# Service URLs
USER_SERVICE_URL=http://localhost:5001
APPOINTMENT_SERVICE_URL=http://localhost:5002
REPORT_SERVICE_URL=http://localhost:5003
```

## API Examples

### User Service
```bash
# Register
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "securepass123",
    "full_name": "John Doe",
    "role": "patient",
    "phone": "+1234567890"
  }'

# Login
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "securepass123"
  }'
```

### Appointment Service
```bash
# Book Appointment
curl -X POST http://localhost:5002/appointments/book \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": 2,
    "appointment_date": "2024-01-20T10:00:00",
    "reason": "Regular checkup"
  }'

# Get History
curl -X GET http://localhost:5002/appointments/history \
  -H "Authorization: Bearer <TOKEN>"
```

### Report Service
```bash
# Upload Report
curl -X POST http://localhost:5003/reports/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@medical_report.pdf" \
  -F "description=X-Ray Report"

# List Reports
curl -X GET http://localhost:5003/reports/list \
  -H "Authorization: Bearer <TOKEN>"

# Download Report
curl -X GET http://localhost:5003/reports/1/download \
  -H "Authorization: Bearer <TOKEN>"
```

## Deployment

### AWS Deployment
- User Service → ECS/ELB
- Appointment Service → ECS/ELB  
- Report Service → ECS/ELB
- Database → RDS PostgreSQL
- File Storage → S3

### CI/CD Pipeline
See [DevSecOps Pipeline](https://github.com/ankit20000/DevSecops_Pipeline) for CI/CD configuration.

## Security Features

- ✅ JWT Authentication
- ✅ Role-Based Access Control (RBAC)
- ✅ Password Hashing (Werkzeug)
- ✅ AWS S3 Signed URLs
- ✅ CORS Support (add as needed)
- ✅ Input Validation
- ✅ SQL Injection Protection (SQLAlchemy ORM)

## Observability & AI Guidance

### Logs vs traces
- **Logs** are structured event records that capture messages, warnings, errors, and request context. They are useful for understanding what happened, why it failed, and which inputs triggered the behavior.
- **Traces** are distributed execution paths that follow a request across service boundaries, showing latency, dependencies, and error boundaries.

### Why observability matters in microservices
- Microservices generate failures across network boundaries, async operations, and third-party integrations.
- Logs and traces together reveal failures, latency hotspots, and cascading errors far faster than ad hoc debugging.
- Correlation IDs connect HTTP requests, database events, and downstream service calls into one timeline.

### What this repository now includes
- Structured JSON logging with `INFO`, `WARN`, `ERROR`, and `DEBUG` level events.
- Request correlation IDs propagated through incoming headers and returned in responses.
- OpenTelemetry instrumentation with OTLP exporter configuration.
- Docker-based collector to receive traces from the Flask services.

### Failure and latency analysis
- **Latency** can be identified by timing fields in logs and by slow spans in traces.
- **Errors** appear as `ERROR` log entries, exception stacks, and failed spans.
- **Cross-service failures** are easier to debug using `request_id` and `trace_id` correlation.

### How AI tools help
- Generate service boilerplate, validation, and error handlers.
- Recommend observability libraries and SDK wiring.
- Improve logging standards with consistent structured fields.
- Suggest performance improvements, slow-path analysis, and debugging hypotheses.
- Speed up root-cause analysis by correlating logs, traces, and service dependencies.

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/
```

## License

MIT License - See LICENSE file

## Contributors

- Built as part of DevSecOps Pipeline Project

## Support

For issues and questions, please open an issue on the GitHub repository.
