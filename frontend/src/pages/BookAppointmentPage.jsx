import React, { useState, useEffect } from 'react';
import {
  Container, Row, Col, Card, Form, Button, Alert, Spinner, Badge
} from 'react-bootstrap';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  FaCalendarAlt, FaUserMd, FaClock, FaNotesMedical, FaArrowLeft, FaCheckCircle
} from 'react-icons/fa';
import { appointmentAPI, authUtils } from '../services/api';

const TIME_SLOTS = [
  '09:00 AM', '09:30 AM', '10:00 AM', '10:30 AM',
  '11:00 AM', '11:30 AM', '12:00 PM', '02:00 PM',
  '02:30 PM', '03:00 PM', '03:30 PM', '04:00 PM',
  '04:30 PM', '05:00 PM',
];

function BookAppointmentPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const user = authUtils.getCurrentUser();

  const [doctors, setDoctors] = useState([]);
  const [loadingDoctors, setLoadingDoctors] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    doctor_id: searchParams.get('doctorId') || '',
    appointment_date: '',
    time: '',
    reason: '',
  });

  useEffect(() => {
    fetchDoctors();
  }, []);

  const fetchDoctors = async () => {
    try {
      const res = await appointmentAPI.listDoctors();
      setDoctors(res.data.doctors || []);
    } catch {
      toast.error('Failed to load doctors');
    } finally {
      setLoadingDoctors(false);
    }
  };

  const selectedDoctor = doctors.find(d => String(d.id) === String(formData.doctor_id));

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleTimeSlot = (slot) => {
    setFormData(prev => ({ ...prev, time: slot }));
    setError('');
  };

  const getTomorrowDate = () => {
    const d = new Date();
    d.setDate(d.getDate() + 1);
    return d.toISOString().split('T')[0];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.doctor_id) { setError('Please select a doctor'); return; }
    if (!formData.appointment_date) { setError('Please select a date'); return; }
    if (!formData.time) { setError('Please select a time slot'); return; }

    setSubmitting(true);
    setError('');
    try {
      await appointmentAPI.bookAppointment({
        doctor_id: parseInt(formData.doctor_id),
        appointment_date: formData.appointment_date,
        time: formData.time,
        reason: formData.reason,
      });
      setSuccess(true);
      toast.success('Appointment booked successfully!');
    } catch (err) {
      const msg = err.response?.data?.message || 'Failed to book appointment';
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (success) {
    return (
      <Container className="py-5">
        <Row className="justify-content-center">
          <Col md={6} className="text-center">
            <Card className="shadow-lg p-4">
              <div style={{ fontSize: '4rem', color: '#28a745', marginBottom: '20px' }}>
                <FaCheckCircle />
              </div>
              <h3 className="mb-3">Appointment Booked!</h3>
              <p className="text-muted mb-4">
                Your appointment with <strong>{selectedDoctor?.full_name}</strong> on{' '}
                <strong>{formData.appointment_date}</strong> at <strong>{formData.time}</strong> is confirmed.
              </p>
              <div className="d-flex gap-3 justify-content-center">
                <Button variant="primary" onClick={() => navigate('/appointments')}>
                  <FaCalendarAlt className="me-2" />View Appointments
                </Button>
                <Button variant="outline-secondary" onClick={() => { setSuccess(false); setFormData({ doctor_id: '', appointment_date: '', time: '', reason: '' }); }}>
                  Book Another
                </Button>
              </div>
            </Card>
          </Col>
        </Row>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <div className="mb-4">
        <Link to="/doctors" className="btn btn-outline-secondary btn-sm me-3">
          <FaArrowLeft className="me-1" /> Back to Doctors
        </Link>
        <h2 className="d-inline-block mb-0">
          <FaCalendarAlt className="me-2 text-primary" />
          Book an Appointment
        </h2>
      </div>

      {user?.role === 'doctor' && (
        <Alert variant="warning">
          Doctors cannot book appointments. Switch to a patient account to book.
        </Alert>
      )}

      <Row>
        <Col lg={8}>
          <Card className="shadow-sm mb-4">
            <Card.Header>
              <FaUserMd className="me-2" />
              Select Doctor &amp; Date
            </Card.Header>
            <Card.Body className="p-4">
              {error && <Alert variant="danger">{error}</Alert>}

              <Form onSubmit={handleSubmit}>
                {/* Doctor Select */}
                <Form.Group className="mb-4">
                  <Form.Label>Doctor</Form.Label>
                  {loadingDoctors ? (
                    <div className="d-flex align-items-center gap-2 text-muted">
                      <Spinner animation="border" size="sm" /> Loading doctors…
                    </div>
                  ) : (
                    <Form.Select
                      name="doctor_id"
                      value={formData.doctor_id}
                      onChange={handleChange}
                      required
                    >
                      <option value="">-- Choose a doctor --</option>
                      {doctors.map(d => (
                        <option key={d.id} value={d.id}>
                          Dr. {d.full_name}{d.specialization ? ` — ${d.specialization}` : ''}
                        </option>
                      ))}
                    </Form.Select>
                  )}
                </Form.Group>

                {/* Date */}
                <Form.Group className="mb-4">
                  <Form.Label><FaCalendarAlt className="me-1" /> Appointment Date</Form.Label>
                  <Form.Control
                    type="date"
                    name="appointment_date"
                    value={formData.appointment_date}
                    onChange={handleChange}
                    min={getTomorrowDate()}
                    required
                  />
                </Form.Group>

                {/* Time Slots */}
                <Form.Group className="mb-4">
                  <Form.Label><FaClock className="me-1" /> Time Slot</Form.Label>
                  <div className="d-flex flex-wrap gap-2 mt-1">
                    {TIME_SLOTS.map(slot => (
                      <Button
                        key={slot}
                        type="button"
                        size="sm"
                        variant={formData.time === slot ? 'primary' : 'outline-primary'}
                        onClick={() => handleTimeSlot(slot)}
                        style={{ minWidth: '90px' }}
                      >
                        {slot}
                      </Button>
                    ))}
                  </div>
                  {formData.time && (
                    <div className="mt-2 small text-success">
                      <FaCheckCircle className="me-1" /> Selected: {formData.time}
                    </div>
                  )}
                </Form.Group>

                {/* Reason */}
                <Form.Group className="mb-4">
                  <Form.Label><FaNotesMedical className="me-1" /> Reason for Visit (optional)</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    name="reason"
                    placeholder="Describe your symptoms or reason for visit…"
                    value={formData.reason}
                    onChange={handleChange}
                  />
                </Form.Group>

                <Button
                  variant="primary"
                  type="submit"
                  className="w-100 py-2"
                  disabled={submitting || user?.role === 'doctor'}
                >
                  {submitting ? (
                    <><Spinner as="span" animation="border" size="sm" className="me-2" />Booking…</>
                  ) : (
                    <><FaCalendarAlt className="me-2" />Confirm Appointment</>
                  )}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>

        {/* Selected Doctor Preview */}
        <Col lg={4}>
          {selectedDoctor ? (
            <Card className="shadow-sm">
              <Card.Header>Selected Doctor</Card.Header>
              <Card.Body className="text-center">
                <div
                  className="mx-auto mb-3 d-flex align-items-center justify-content-center"
                  style={{
                    width: 80, height: 80, borderRadius: '50%',
                    background: 'linear-gradient(135deg, #0066cc, #00cc99)',
                    color: 'white', fontSize: '2rem'
                  }}
                >
                  <FaUserMd />
                </div>
                <h5>{selectedDoctor.full_name}</h5>
                {selectedDoctor.specialization && (
                  <Badge bg="primary" className="mb-2">{selectedDoctor.specialization}</Badge>
                )}
                {selectedDoctor.phone && (
                  <p className="small text-muted mb-1">📞 {selectedDoctor.phone}</p>
                )}
                {selectedDoctor.email && (
                  <p className="small text-muted mb-0">✉️ {selectedDoctor.email}</p>
                )}
              </Card.Body>
            </Card>
          ) : (
            <Card className="shadow-sm">
              <Card.Body className="text-center text-muted py-5">
                <FaUserMd size={40} className="mb-3 opacity-25" />
                <p>Select a doctor to see details</p>
              </Card.Body>
            </Card>
          )}

          {formData.appointment_date && formData.time && (
            <Card className="shadow-sm mt-3">
              <Card.Header>Appointment Summary</Card.Header>
              <Card.Body className="small">
                <p className="mb-1"><strong>Date:</strong> {formData.appointment_date}</p>
                <p className="mb-1"><strong>Time:</strong> {formData.time}</p>
                {formData.reason && <p className="mb-0"><strong>Reason:</strong> {formData.reason}</p>}
              </Card.Body>
            </Card>
          )}
        </Col>
      </Row>
    </Container>
  );
}

export default BookAppointmentPage;
