import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert, Spinner } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { userAPI, authUtils } from '../services/api';
import { FaEnvelope, FaLock, FaSignInAlt } from 'react-icons/fa';

function LoginPage({ onLoginSuccess }) {
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await userAPI.login(formData.email, formData.password);
      
      if (response.status === 200 && response.data.access_token) {
        // Save login data
        authUtils.saveLoginData(response.data.access_token, response.data.user);
        
        toast.success(`Welcome back, ${response.data.user.full_name}!`);
        onLoginSuccess();
        navigate('/dashboard');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Login failed. Please check your credentials.';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container className="py-5">
      <Row className="justify-content-center">
        <Col md={5}>
          <Card className="shadow-lg">
            <Card.Header>
              <h4 className="mb-0">
                <FaSignInAlt className="me-2" />
                Login to Your Account
              </h4>
            </Card.Header>
            <Card.Body className="p-4">
              {error && (
                <Alert variant="danger" className="mb-4">
                  {error}
                </Alert>
              )}

              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Email Address</Form.Label>
                  <div className="input-group">
                    <span className="input-group-text">
                      <FaEnvelope />
                    </span>
                    <Form.Control
                      type="email"
                      name="email"
                      placeholder="Enter your email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                    />
                  </div>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Password</Form.Label>
                  <div className="input-group">
                    <span className="input-group-text">
                      <FaLock />
                    </span>
                    <Form.Control
                      type="password"
                      name="password"
                      placeholder="Enter your password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                    />
                  </div>
                </Form.Group>

                <Button 
                  variant="primary" 
                  type="submit" 
                  className="w-100 py-2 mb-3"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Spinner as="span" animation="border" size="sm" className="me-2" />
                      Logging in...
                    </>
                  ) : (
                    <>
                      <FaSignInAlt className="me-2" />
                      Login
                    </>
                  )}
                </Button>
              </Form>

              <hr className="my-3" />

              <p className="text-center mb-0">
                Don't have an account?{' '}
                <Link to="/register" className="text-primary fw-bold">
                  Register here
                </Link>
              </p>
            </Card.Body>
          </Card>

          <Alert variant="info" className="mt-4">
            <strong>Demo Credentials:</strong>
            <br />
            Patient: patient@example.com / pass123456
            <br />
            Doctor: doctor@example.com / pass123456
          </Alert>
        </Col>
      </Row>
    </Container>
  );
}

export default LoginPage;
