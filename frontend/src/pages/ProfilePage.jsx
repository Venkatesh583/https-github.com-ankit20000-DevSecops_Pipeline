import React, { useState, useEffect } from 'react';
import {
  Container, Row, Col, Card, Form, Button, Spinner, Alert, Badge
} from 'react-bootstrap';
import { toast } from 'react-toastify';
import {
  FaUser, FaEnvelope, FaPhone, FaUserMd, FaEdit, FaSave, FaShieldAlt
} from 'react-icons/fa';
import { userAPI, authUtils } from '../services/api';

const ROLE_COLORS = { patient: 'primary', doctor: 'success', admin: 'danger' };

function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({ full_name: '', phone: '' });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await userAPI.getProfile();
      setProfile(res.data);
      setFormData({ full_name: res.data.full_name || '', phone: res.data.phone || '' });
    } catch {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!formData.full_name.trim()) { toast.error('Name is required'); return; }
    setSaving(true);
    try {
      const res = await userAPI.updateProfile(formData);
      setProfile(res.data.user);
      // Update localStorage so navbar name updates too
      const stored = authUtils.getCurrentUser();
      if (stored) {
        authUtils.saveLoginData(authUtils.getToken(), { ...stored, ...res.data.user });
      }
      toast.success('Profile updated successfully!');
      setEditing(false);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" />
        <p className="mt-2 text-muted">Loading profile…</p>
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-5">
        <Alert variant="danger">{error}</Alert>
      </Container>
    );
  }

  const initials = profile?.full_name
    ? profile.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  return (
    <Container className="py-5">
      <h2 className="mb-4">
        <FaUser className="me-2 text-primary" />
        My Profile
      </h2>

      <Row>
        {/* Avatar + Role Card */}
        <Col lg={4} className="mb-4">
          <Card className="shadow-sm text-center">
            <Card.Body className="py-5">
              <div
                className="mx-auto mb-3 d-flex align-items-center justify-content-center fw-bold"
                style={{
                  width: 100, height: 100, borderRadius: '50%',
                  background: 'linear-gradient(135deg, #0066cc, #00cc99)',
                  color: 'white', fontSize: '2.2rem',
                }}
              >
                {initials}
              </div>
              <h4 className="mb-1">{profile?.full_name}</h4>
              <p className="text-muted mb-3">{profile?.email}</p>
              <Badge bg={ROLE_COLORS[profile?.role] || 'secondary'} className="px-3 py-2 text-uppercase">
                {profile?.role}
              </Badge>
              {profile?.role === 'doctor' && profile?.specialization && (
                <div className="mt-3">
                  <Badge bg="info" text="dark">{profile.specialization}</Badge>
                </div>
              )}
              <div className="mt-4 small text-muted">
                <FaShieldAlt className="me-1" />
                Account {profile?.is_active ? 'Active' : 'Inactive'}
              </div>
            </Card.Body>
          </Card>
        </Col>

        {/* Edit Profile */}
        <Col lg={8} className="mb-4">
          <Card className="shadow-sm">
            <Card.Header className="d-flex justify-content-between align-items-center">
              <span><FaEdit className="me-2" />Profile Details</span>
              {!editing && (
                <Button size="sm" variant="outline-primary" onClick={() => setEditing(true)}>
                  <FaEdit className="me-1" />Edit
                </Button>
              )}
            </Card.Header>
            <Card.Body className="p-4">
              <Form onSubmit={handleSave}>
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label><FaUser className="me-1" />Full Name</Form.Label>
                      {editing ? (
                        <Form.Control
                          type="text"
                          name="full_name"
                          value={formData.full_name}
                          onChange={handleChange}
                          required
                        />
                      ) : (
                        <p className="form-control-plaintext fw-semibold">{profile?.full_name || '—'}</p>
                      )}
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label><FaPhone className="me-1" />Phone Number</Form.Label>
                      {editing ? (
                        <Form.Control
                          type="tel"
                          name="phone"
                          value={formData.phone}
                          onChange={handleChange}
                          placeholder="Enter phone number"
                        />
                      ) : (
                        <p className="form-control-plaintext">{profile?.phone || <span className="text-muted">Not provided</span>}</p>
                      )}
                    </Form.Group>
                  </Col>
                </Row>

                <Form.Group className="mb-3">
                  <Form.Label><FaEnvelope className="me-1" />Email Address</Form.Label>
                  <p className="form-control-plaintext text-muted">
                    {profile?.email}
                    <small className="ms-2 text-muted">(cannot be changed)</small>
                  </p>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Role</Form.Label>
                  <p className="form-control-plaintext text-capitalize">
                    <Badge bg={ROLE_COLORS[profile?.role] || 'secondary'}>{profile?.role}</Badge>
                  </p>
                </Form.Group>

                {profile?.role === 'doctor' && (
                  <Form.Group className="mb-3">
                    <Form.Label><FaUserMd className="me-1" />Specialization</Form.Label>
                    <p className="form-control-plaintext">{profile?.specialization || <span className="text-muted">Not set</span>}</p>
                  </Form.Group>
                )}

                {editing && (
                  <div className="d-flex gap-2 mt-4">
                    <Button variant="primary" type="submit" disabled={saving}>
                      {saving
                        ? <><Spinner as="span" animation="border" size="sm" className="me-2" />Saving…</>
                        : <><FaSave className="me-2" />Save Changes</>
                      }
                    </Button>
                    <Button variant="outline-secondary" type="button" onClick={() => { setEditing(false); setFormData({ full_name: profile?.full_name || '', phone: profile?.phone || '' }); }}>
                      Cancel
                    </Button>
                  </div>
                )}
              </Form>
            </Card.Body>
          </Card>

          {/* Account Info Card */}
          <Card className="shadow-sm mt-3">
            <Card.Header>Account Information</Card.Header>
            <Card.Body>
              <Row className="small text-muted">
                <Col md={6}>
                  <p className="mb-1"><strong>User ID:</strong> #{profile?.id}</p>
                  <p className="mb-1">
                    <strong>Status:</strong>{' '}
                    <Badge bg={profile?.is_active ? 'success' : 'danger'}>
                      {profile?.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </p>
                </Col>
                <Col md={6}>
                  {profile?.created_at && (
                    <p className="mb-1">
                      <strong>Member since:</strong> {new Date(profile.created_at).toLocaleDateString()}
                    </p>
                  )}
                </Col>
              </Row>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
}

export default ProfilePage;
