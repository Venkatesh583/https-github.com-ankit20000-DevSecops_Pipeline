import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Spinner, Alert, Badge, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { FaUserMd, FaPhone, FaEnvelope, FaStar, FaArrowRight } from 'react-icons/fa';
import { appointmentAPI } from '../services/api';
import { toast } from 'react-toastify';

function DoctorsPage() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterSpecialty, setFilterSpecialty] = useState('');
  const [specialties, setSpecialties] = useState([]);

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      setLoading(true);
      const response = await appointmentAPI.listDoctors();
      const doctorList = response.data.doctors || [];
      setDoctors(doctorList);

      // Extract unique specialties
      const uniqueSpecialties = [...new Set(doctorList.map(d => d.specialization).filter(Boolean))];
      setSpecialties(uniqueSpecialties);
    } catch (err) {
      setError('Failed to load doctors');
      toast.error('Failed to load doctors');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredDoctors = filterSpecialty
    ? doctors.filter(d => d.specialization === filterSpecialty)
    : doctors;

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
      <h2 className="mb-4">
        <FaUserMd className="me-2" />
        Find Your Doctor
      </h2>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Filter Section */}
      {specialties.length > 0 && (
        <Row className="mb-4">
          <Col md={12}>
            <Card className="bg-light">
              <Card.Body>
                <h6 className="mb-3">Filter by Specialty</h6>
                <div className="d-flex flex-wrap gap-2">
                  <Button
                    variant={filterSpecialty === '' ? 'primary' : 'outline-primary'}
                    onClick={() => setFilterSpecialty('')}
                    size="sm"
                  >
                    All Doctors ({doctors.length})
                  </Button>
                  {specialties.map(specialty => (
                    <Button
                      key={specialty}
                      variant={filterSpecialty === specialty ? 'primary' : 'outline-primary'}
                      onClick={() => setFilterSpecialty(specialty)}
                      size="sm"
                    >
                      {specialty}
                    </Button>
                  ))}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {/* Doctors Grid */}
      {filteredDoctors.length > 0 ? (
        <Row>
          {filteredDoctors.map(doctor => (
            <Col md={6} lg={4} key={doctor.id} className="mb-4">
              <Card className="h-100 shadow-sm">
                <Card.Body>
                  <div className="d-flex align-items-start mb-3">
                    <div
                      style={{
                        width: '60px',
                        height: '60px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #0066cc, #004499)',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '1.5rem',
                        marginRight: '15px'
                      }}
                    >
                      <FaUserMd />
                    </div>
                    <div className="flex-grow-1">
                      <h5 className="mb-1">{doctor.full_name}</h5>
                      {doctor.specialization && (
                        <Badge bg="primary" className="mb-2">
                          {doctor.specialization}
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="mb-3 small">
                    {doctor.phone && (
                      <p className="mb-2">
                        <FaPhone className="me-2 text-primary" />
                        {doctor.phone}
                      </p>
                    )}
                    {doctor.email && (
                      <p className="mb-0">
                        <FaEnvelope className="me-2 text-primary" />
                        {doctor.email}
                      </p>
                    )}
                  </div>

                  <div className="d-flex align-items-center mb-3">
                    <FaStar className="text-warning me-2" />
                    <span className="small text-muted">4.8 (120 reviews)</span>
                  </div>
                </Card.Body>
                <Card.Footer className="bg-white border-top">
                  <Link
                    to={`/book-appointment?doctorId=${doctor.id}`}
                    className="btn btn-primary btn-sm w-100"
                  >
                    Book Appointment <FaArrowRight className="ms-2" />
                  </Link>
                </Card.Footer>
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">
            <FaUserMd />
          </div>
          <h5>No doctors found</h5>
          <p>Try a different filter</p>
        </div>
      )}
    </Container>
  );
}

export default DoctorsPage;
