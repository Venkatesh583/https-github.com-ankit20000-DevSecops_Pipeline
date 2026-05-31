# Quick Start Guide - Healthcare Microservices

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Docker & Docker Compose (optional)

### 1️⃣ Clone & Setup

```bash
# Clone repository
cd healthcare-microservices

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies for all services
cd user-service && pip install -r requirements.txt
cd ../appointment-service && pip install -r requirements.txt
cd ../report-service && pip install -r requirements.txt
cd ..
```

### 2️⃣ Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings
# At minimum set:
# - JWT_SECRET_KEY
# - DATABASE_URL (PostgreSQL)
# - AWS credentials (for S3)
```

### 3️⃣ Initialize Database

```bash
# Create PostgreSQL database
createdb healthcare_db

# Services create tables automatically on first run
```

### 4️⃣ Run Services

```bash
# Terminal 1 - User Service
cd user-service
python app.py
# Available at http://localhost:5001

# Terminal 2 - Appointment Service
cd appointment-service
python app.py
# Available at http://localhost:5002

# Terminal 3 - Report Service
cd report-service
python app.py
# Available at http://localhost:5003
```

### 5️⃣ Test the APIs

```bash
# User Registration
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "securepass123",
    "full_name": "John Doe",
    "role": "patient"
  }'

# User Login
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@example.com",
    "password": "securepass123"
  }'

# Health Check
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

---

## 🧪 Running Tests

### Quick Test Commands

```bash
# Run all unit tests
pytest -v

# Run specific service tests
cd user-service && pytest test_app.py -v

# Run with coverage
pytest -v --cov=. --cov-report=html

# Using helper scripts
./run_tests.sh --all              # Linux/Mac
run_tests.bat --all               # Windows

# Run integration tests
./run_tests.sh --integration
run_tests.bat --integration

# Run with coverage report
./run_tests.sh --coverage
run_tests.bat --coverage
```

---

## 🐳 Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Run tests in containers
docker exec user-service pytest test_app.py -v
docker exec appointment-service pytest test_app.py -v
docker exec report-service pytest test_app.py -v
```

---

## 📚 API Quick Reference

### Authentication
```bash
# Get JWT token
TOKEN=$(curl -s -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass"}' \
  | jq -r '.access_token')

# Use token in requests
curl -H "Authorization: Bearer $TOKEN" http://localhost:5001/users/profile
```

### User Service
```bash
# Register
POST /register

# Login
POST /login

# Get profile
GET /users/profile

# List doctors
GET /doctors

# Get doctor
GET /doctors/<id>
```

### Appointment Service
```bash
# List doctors
GET /doctors

# Book appointment
POST /appointments

# View history
GET /appointments/history

# Confirm appointment
POST /appointments/<id>/confirm

# Cancel appointment
POST /appointments/<id>/cancel
```

### Report Service
```bash
# Upload report
POST /reports/upload

# List reports
GET /reports/list

# Download report
GET /reports/<id>/download

# Delete report
DELETE /reports/<id>/delete
```

---

## 🔍 Debugging

### Check Service Health
```bash
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

### View Logs
```bash
# User Service logs
tail -f /tmp/user-service.log

# With structured logging
tail -f /tmp/user-service.log | jq '.'
```

### Database Connection
```bash
# Connect to PostgreSQL
psql healthcare_db

# List tables
\dt

# Check users
SELECT * FROM users;
SELECT * FROM appointments;
SELECT * FROM medical_reports;
```

---

## 📋 Common Tasks

### Add a New User
```bash
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@example.com",
    "password": "docpass123",
    "full_name": "Dr. Smith",
    "role": "doctor",
    "specialization": "Cardiology"
  }'
```

### Book an Appointment
```bash
curl -X POST http://localhost:5002/appointments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "doctor_id": 2,
    "appointment_date": "2025-06-15",
    "time": "10:00 AM",
    "reason": "Routine checkup"
  }'
```

### Upload a Report
```bash
curl -X POST http://localhost:5003/reports/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/report.pdf" \
  -F "description=Medical report"
```

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :5001
kill <PID>

# Or use different ports
# Edit config.py in each service
```

### Database Connection Error
```bash
# Check PostgreSQL is running
psql -U postgres

# Check DATABASE_URL in .env
# Format: postgresql://user:password@host:port/database
```

### JWT Token Expired
```bash
# Get new token
curl -X POST http://localhost:5001/login ...

# Token expires in 1 hour (configurable)
# Check JWT_ACCESS_TOKEN_EXPIRES in config.py
```

### S3 Upload Fails
```bash
# Verify AWS credentials in .env
# Check bucket exists and permissions
# Enable debug logging to see errors
```

---

## 📖 Documentation

- **API_AND_TESTING.md** - Complete API documentation and testing guide
- **COMPLETION_SUMMARY.md** - Project completion summary
- **README.md** - Original project documentation

---

## 🎯 Next Steps

1. ✅ Verify all services are running
2. ✅ Run test suite
3. ✅ Test APIs with provided curl commands
4. ✅ Review documentation
5. ✅ Deploy to your environment

---

## 💡 Tips

- Use Postman or Insomnia for easier API testing
- Enable JSON logging output with `tail -f | jq`
- Set `FLASK_DEBUG=true` for development
- Use `--reload` flag with Flask for auto-reload
- Check `.env.example` for all available options

---

## 📞 Support

For issues or questions:
1. Check API_AND_TESTING.md documentation
2. Review test files for examples
3. Check service logs for errors
4. Verify environment configuration

---

Happy coding! 🎉

