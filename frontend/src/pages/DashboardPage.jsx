import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Alert, Spinner } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { FaCalendarAlt, FaUserMd, FaFileAlt, FaChartLine, FaArrowRight } from 'react-icons/fa';
import { appointmentAPI, reportAPI, authUtils } from '../services/api';

function DashboardPage() {
  const [stats, setStats] = useState({
    totalAppointments: 0,
    pendingAppointments: 0,
    totalReports: 0,
    doctors: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const user = authUtils.getCurrentUser();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [appointmentRes, reportRes, doctorRes] = await Promise.all([
        appointmentAPI.getHistory(),
        reportAPI.getReports(),
        appointmentAPI.listDoctors()
      ]);

      const appointments = appointmentRes.data.appointments || [];
      const reports = reportRes.data.reports || [];
      const doctors = doctorRes.data.doctors || [];

      setStats({
        totalAppointments: appointments.length,
        pendingAppointments: appointments.filter(a => a.status === 'pending').length,
        totalReports: reports.length,
        doctors: doctors.length
      });
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container className="py-5">
        <div className="spinner-container">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
        </div>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      {/* Welcome Section */}
      <div className="hero mb-5">
        <h1>Welcome back, {user?.full_name}!</h1>
        <p>Manage your healthcare journey with us</p>
      </div>

      {error && (
        <Alert variant="warning" className="mb-4">
          {error}
        </Alert>
      )}

      {/* Stats Section */}
      <Row className="mb-5">
        <Col md={6} lg={3} className="mb-3">
          <div className="stat-card">
            <FaCalendarAlt style={{ color: '#0066cc', fontSize: '2rem' }} />
            <h3>{stats.totalAppointments}</h3>
            <p>Total Appointments</p>
          </div>
        </Col>
        <Col md={6} lg={3} className="mb-3">
          <div className="stat-card">
            <FaCalendarAlt style={{ color: '#ffc107', fontSize: '2rem' }} />
            <h3>{stats.pendingAppointments}</h3>
            <p>Pending Appointments</p>
          </div>
        </Col>
        <Col md={6} lg={3} className="mb-3">
          <div className="stat-card">
            <FaFileAlt style={{ color: '#28a745', fontSize: '2rem' }} />
            <h3>{stats.totalReports}</h3>
            <p>Medical Reports</p>
          </div>
        </Col>
        <Col md={6} lg={3} className="mb-3">
          <div className="stat-card">
            <FaUserMd style={{ color: '#dc3545', fontSize: '2rem' }} />
            <h3>{stats.doctors}</h3>
            <p>Available Doctors</p>
          </div>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row>
        <Col lg={6} className="mb-4">
          <Card className="h-100">
            <Card.Header>
              <FaCalendarAlt className="me-2" />
              Appointments
            </Card.Header>
            <Card.Body>
              <p>Manage and track your medical appointments</p>
              {stats.pendingAppointments > 0 && (
                <Alert variant="warning" className="small mb-3">
                  You have {stats.pendingAppointments} pending appointment(s)
                </Alert>
              )}
            </Card.Body>
            <Card.Footer className="bg-white border-top">
              <Link to="/appointments" className="btn btn-primary">
                View Appointments <FaArrowRight className="ms-2" />
              </Link>
            </Card.Footer>
          </Card>
        </Col>

        <Col lg={6} className="mb-4">
          <Card className="h-100">
            <Card.Header>
              <FaUserMd className="me-2" />
              Book Appointment
            </Card.Header>
            <Card.Body>
              <p>Schedule an appointment with available doctors</p>
              <p className="text-muted small mb-0">
                Browse our doctors and find the perfect time for your visit
              </p>
            </Card.Body>
            <Card.Footer className="bg-white border-top">
              <Link to="/book-appointment" className="btn btn-secondary">
                Book Now <FaArrowRight className="ms-2" />
              </Link>
            </Card.Footer>
          </Card>
        </Col>
      </Row>

      <Row>
        <Col lg={6} className="mb-4">
          <Card className="h-100">
            <Card.Header>
              <FaUserMd className="me-2" />
              Find Doctors
            </Card.Header>
            <Card.Body>
              <p>Search for specialized doctors</p>
              <p className="text-muted small mb-0">
                Find doctors by specialty and availability
              </p>
            </Card.Body>
            <Card.Footer className="bg-white border-top">
              <Link to="/doctors" className="btn btn-primary">
                View All Doctors <FaArrowRight className="ms-2" />
              </Link>
            </Card.Footer>
          </Card>
        </Col>

        <Col lg={6} className="mb-4">
          <Card className="h-100">
            <Card.Header>
              <FaFileAlt className="me-2" />
              Medical Reports
            </Card.Header>
            <Card.Body>
              <p>Upload and manage your medical reports</p>
              <p className="text-muted small mb-0">
                Securely store and share your health documents
              </p>
            </Card.Body>
            <Card.Footer className="bg-white border-top">
              <Link to="/reports" className="btn btn-success">
                Manage Reports <FaArrowRight className="ms-2" />
              </Link>
            </Card.Footer>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default DashboardPage;
