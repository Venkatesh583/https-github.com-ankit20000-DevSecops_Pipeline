import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import { FaHeartbeat, FaFacebook, FaTwitter, FaLinkedin, FaEnvelope, FaPhone } from 'react-icons/fa';

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="mt-5">
      <Container>
        <Row className="mb-4">
          <Col md={3} className="mb-3">
            <h5 className="d-flex align-items-center">
              <FaHeartbeat className="me-2" />
              HealthCare Pro
            </h5>
            <p className="small">
              Your trusted healthcare companion for managing appointments, doctors, and medical reports.
            </p>
          </Col>

          <Col md={3} className="mb-3">
            <h5>Quick Links</h5>
            <ul className="list-unstyled">
              <li><a href="/dashboard">Dashboard</a></li>
              <li><a href="/doctors">Find Doctors</a></li>
              <li><a href="/appointments">My Appointments</a></li>
              <li><a href="/reports">Medical Reports</a></li>
            </ul>
          </Col>

          <Col md={3} className="mb-3">
            <h5>Support</h5>
            <ul className="list-unstyled">
              <li><a href="#privacy">Privacy Policy</a></li>
              <li><a href="#terms">Terms & Conditions</a></li>
              <li><a href="#faq">FAQs</a></li>
              <li><a href="#contact">Contact Us</a></li>
            </ul>
          </Col>

          <Col md={3} className="mb-3">
            <h5>Contact Info</h5>
            <p className="small">
              <FaPhone className="me-2" />
              +1 (555) 123-4567
            </p>
            <p className="small">
              <FaEnvelope className="me-2" />
              support@healthcarepro.com
            </p>
            <div className="mt-3">
              <a href="#facebook" className="me-3"><FaFacebook size={20} /></a>
              <a href="#twitter" className="me-3"><FaTwitter size={20} /></a>
              <a href="#linkedin"><FaLinkedin size={20} /></a>
            </div>
          </Col>
        </Row>

        <hr className="my-4" style={{ borderColor: '#444' }} />

        <Row>
          <Col md={6}>
            <p className="small mb-0">
              &copy; {currentYear} HealthCare Pro. All rights reserved.
            </p>
          </Col>
          <Col md={6} className="text-md-end">
            <p className="small mb-0">
              Built with <span style={{ color: 'var(--secondary-color)' }}>❤️</span> for healthcare excellence
            </p>
          </Col>
        </Row>
      </Container>
    </footer>
  );
}

export default Footer;
