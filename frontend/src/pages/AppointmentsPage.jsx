import React, { useState, useEffect } from 'react';
import {
  Container, Row, Col, Card, Table, Badge, Button, Spinner, Alert, Modal, Form
} from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import {
  FaCalendarAlt, FaUserMd, FaClock, FaCheckCircle, FaTimesCircle,
  FaPlus, FaNotesMedical, FaFilter
} from 'react-icons/fa';
import { appointmentAPI, authUtils } from '../services/api';

const STATUS_VARIANT = {
  pending: 'warning',
  confirmed: 'success',
  completed: 'primary',
  cancelled: 'danger',
};

function AppointmentsPage() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [confirmModal, setConfirmModal] = useState({ show: false, id: null, notes: '' });
  const [actionLoading, setActionLoading] = useState(false);
  const user = authUtils.getCurrentUser();
  const isDoctor = user?.role === 'doctor';

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const res = await appointmentAPI.getHistory();
      setAppointments(res.data.appointments || []);
    } catch {
      setError('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm('Cancel this appointment?')) return;
    setActionLoading(true);
    try {
      await appointmentAPI.cancelAppointment(id);
      toast.success('Appointment cancelled');
      fetchAppointments();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to cancel');
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirm = async () => {
    setActionLoading(true);
    try {
      await appointmentAPI.confirmAppointment(confirmModal.id, confirmModal.notes);
      toast.success('Appointment confirmed');
      setConfirmModal({ show: false, id: null, notes: '' });
      fetchAppointments();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to confirm');
    } finally {
      setActionLoading(false);
    }
  };

  const filtered = filterStatus === 'all'
    ? appointments
    : appointments.filter(a => a.status === filterStatus);

  const stats = {
    total: appointments.length,
    pending: appointments.filter(a => a.status === 'pending').length,
    confirmed: appointments.filter(a => a.status === 'confirmed').length,
    completed: appointments.filter(a => a.status === 'completed').length,
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" role="status" />
        <p className="mt-2 text-muted">Loading appointments…</p>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <h2 className="mb-0">
          <FaCalendarAlt className="me-2 text-primary" />
          {isDoctor ? 'Patient Appointments' : 'My Appointments'}
        </h2>
        {!isDoctor && (
          <Link to="/book-appointment" className="btn btn-primary">
            <FaPlus className="me-2" />Book Appointment
          </Link>
        )}
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Stats Row */}
      <Row className="mb-4">
        {[
          { label: 'Total', value: stats.total, icon: <FaCalendarAlt />, color: '#0066cc' },
          { label: 'Pending', value: stats.pending, icon: <FaClock />, color: '#ffc107' },
          { label: 'Confirmed', value: stats.confirmed, icon: <FaCheckCircle />, color: '#28a745' },
          { label: 'Completed', value: stats.completed, icon: <FaUserMd />, color: '#6f42c1' },
        ].map(s => (
          <Col md={6} lg={3} className="mb-3" key={s.label}>
            <div className="stat-card">
              <div style={{ color: s.color, fontSize: '1.8rem' }}>{s.icon}</div>
              <h3 style={{ color: s.color }}>{s.value}</h3>
              <p>{s.label}</p>
            </div>
          </Col>
        ))}
      </Row>

      {/* Filter */}
      <Card className="shadow-sm mb-4">
        <Card.Body className="py-3">
          <div className="d-flex align-items-center gap-2 flex-wrap">
            <FaFilter className="text-muted" />
            {['all', 'pending', 'confirmed', 'completed', 'cancelled'].map(s => (
              <Button
                key={s}
                size="sm"
                variant={filterStatus === s ? 'primary' : 'outline-secondary'}
                onClick={() => setFilterStatus(s)}
                className="text-capitalize"
              >
                {s === 'all' ? `All (${stats.total})` : s}
              </Button>
            ))}
          </div>
        </Card.Body>
      </Card>

      {/* Table */}
      <Card className="shadow-sm">
        <Card.Body className="p-0">
          {filtered.length === 0 ? (
            <div className="empty-state py-5">
              <div className="empty-state-icon"><FaCalendarAlt /></div>
              <h5>No appointments found</h5>
              {!isDoctor && (
                <Link to="/book-appointment" className="btn btn-primary mt-3">
                  <FaPlus className="me-2" />Book Your First Appointment
                </Link>
              )}
            </div>
          ) : (
            <div className="table-responsive">
              <Table hover className="mb-0">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>{isDoctor ? 'Patient' : 'Doctor'}</th>
                    <th>Specialization</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Reason</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((appt, idx) => (
                    <tr key={appt.id}>
                      <td className="text-muted small">{idx + 1}</td>
                      <td>
                        <FaUserMd className="me-1 text-primary" />
                        {isDoctor ? `Patient #${appt.patient_id}` : appt.doctor_name || `Dr. #${appt.doctor_id}`}
                      </td>
                      <td>
                        {appt.specialization
                          ? <Badge bg="info" text="dark">{appt.specialization}</Badge>
                          : <span className="text-muted small">—</span>}
                      </td>
                      <td>{appt.appointment_date ? new Date(appt.appointment_date).toLocaleDateString() : '—'}</td>
                      <td>{appt.time_slot || '—'}</td>
                      <td>
                        <Badge bg={STATUS_VARIANT[appt.status] || 'secondary'} className="text-capitalize">
                          {appt.status}
                        </Badge>
                      </td>
                      <td className="small text-muted" style={{ maxWidth: 150 }}>
                        <span title={appt.reason}>
                          {appt.reason ? appt.reason.substring(0, 40) + (appt.reason.length > 40 ? '…' : '') : '—'}
                        </span>
                      </td>
                      <td>
                        {appt.status === 'pending' && !isDoctor && (
                          <Button
                            size="sm" variant="outline-danger"
                            onClick={() => handleCancel(appt.id)}
                            disabled={actionLoading}
                          >
                            <FaTimesCircle className="me-1" />Cancel
                          </Button>
                        )}
                        {appt.status === 'pending' && isDoctor && (
                          <Button
                            size="sm" variant="outline-success"
                            onClick={() => setConfirmModal({ show: true, id: appt.id, notes: '' })}
                          >
                            <FaCheckCircle className="me-1" />Confirm
                          </Button>
                        )}
                        {appt.status === 'confirmed' && !isDoctor && (
                          <Button
                            size="sm" variant="outline-danger"
                            onClick={() => handleCancel(appt.id)}
                            disabled={actionLoading}
                          >
                            <FaTimesCircle className="me-1" />Cancel
                          </Button>
                        )}
                        {(appt.status === 'completed' || appt.status === 'cancelled') && (
                          <span className="text-muted small">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Confirm Modal (Doctor) */}
      <Modal show={confirmModal.show} onHide={() => setConfirmModal({ show: false, id: null, notes: '' })} centered>
        <Modal.Header closeButton>
          <Modal.Title><FaCheckCircle className="me-2 text-success" />Confirm Appointment</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group>
            <Form.Label><FaNotesMedical className="me-1" />Notes (optional)</Form.Label>
            <Form.Control
              as="textarea" rows={3}
              placeholder="Add any notes for the patient…"
              value={confirmModal.notes}
              onChange={e => setConfirmModal(prev => ({ ...prev, notes: e.target.value }))}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setConfirmModal({ show: false, id: null, notes: '' })}>
            Cancel
          </Button>
          <Button variant="success" onClick={handleConfirm} disabled={actionLoading}>
            {actionLoading ? <Spinner as="span" animation="border" size="sm" /> : 'Confirm Appointment'}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}

export default AppointmentsPage;
