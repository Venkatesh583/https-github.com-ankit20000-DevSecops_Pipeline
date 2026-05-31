import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import { FaHeartbeat, FaSignOutAlt, FaUser } from 'react-icons/fa';
import { authUtils } from '../services/api';

function Navigation({ isLoggedIn, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authUtils.getCurrentUser();

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;

  return (
    <Navbar expand="lg" sticky="top" className="navbar-dark">
      <Container>
        <Navbar.Brand as={Link} to="/" className="d-flex align-items-center">
          <FaHeartbeat className="me-2" style={{ fontSize: '1.5rem' }} />
          <span>HealthCare Pro</span>
        </Navbar.Brand>

        <Navbar.Toggle aria-controls="basic-navbar-nav" />

        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            {isLoggedIn ? (
              <>
                <Nav.Link 
                  as={Link} 
                  to="/dashboard"
                  className={isActive('/dashboard') ? 'active' : ''}
                >
                  Dashboard
                </Nav.Link>

                <Nav.Link 
                  as={Link} 
                  to="/doctors"
                  className={isActive('/doctors') ? 'active' : ''}
                >
                  Doctors
                </Nav.Link>

                <Nav.Link 
                  as={Link} 
                  to="/appointments"
                  className={isActive('/appointments') ? 'active' : ''}
                >
                  Appointments
                </Nav.Link>

                <Nav.Link 
                  as={Link} 
                  to="/reports"
                  className={isActive('/reports') ? 'active' : ''}
                >
                  Medical Reports
                </Nav.Link>

                <Nav.Link 
                  as={Link} 
                  to="/profile"
                  className={isActive('/profile') ? 'active' : ''}
                >
                  <FaUser className="me-1" />
                  Profile
                </Nav.Link>

                {user && (
                  <Nav.Text className="ms-3 me-3" style={{ color: 'white' }}>
                    Welcome, <strong>{user.full_name}</strong> 
                    <span className="badge badge-info ms-2" style={{ fontSize: '0.7rem' }}>
                      {user.role.toUpperCase()}
                    </span>
                  </Nav.Text>
                )}

                <Button 
                  variant="outline-light" 
                  onClick={handleLogout}
                  className="ms-2"
                >
                  <FaSignOutAlt className="me-1" />
                  Logout
                </Button>
              </>
            ) : (
              <>
                <Nav.Link as={Link} to="/login">
                  Login
                </Nav.Link>
                <Nav.Link as={Link} to="/register">
                  Register
                </Nav.Link>
                <Nav.Link as={Link} to="/health">
                  Health Status
                </Nav.Link>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default Navigation;
