import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Spinner, Badge } from 'react-bootstrap';
import { toast } from 'react-toastify';
import {
  FaHeartbeat, FaCheckCircle, FaTimesCircle, FaSync, FaServer, FaDatabase
} from 'react-icons/fa';
import { userAPI, appointmentAPI, reportAPI } from '../services/api';

const SERVICES = [
  {
    key: 'userService',
    name: 'User Service',
    port: '5001',
    description: 'Authentication, registration, doctor & user profiles',
    icon: <FaServer className="me-2" />,
    check: () => userAPI.healthCheck(),
  },
  {
    key: 'appointmentService',
    name: 'Appointment Service',
    port: '5002',
    description: 'Appointment booking, management, and scheduling',
    icon: <FaServer className="me-2" />,
    check: () => appointmentAPI.healthCheck(),
  },
  {
    key: 'reportService',
    name: 'Report Service',
    port: '5003',
    description: 'Medical report upload, storage (AWS S3), and retrieval',
    icon: <FaDatabase className="me-2" />,
    check: () => reportAPI.healthCheck(),
  },
];

function ServiceCard({ service, status, latency, checking }) {
  const up = status === 'healthy';
  const unknown = status === 'unknown';

  return (
    <Col md={4} className="mb-4">
      <Card className={`shadow-sm h-100 border-start border-4 ${up ? 'border-success' : unknown ? 'border-secondary' : 'border-danger'}`}>
        <Card.Body>
          <div className="d-flex justify-content-between align-items-start mb-3">
            <div>
              <h5 className="mb-1">
                {service.icon}
                {service.name}
              </h5>
              <small className="text-muted">Port {service.port}</small>
            </div>
            {checking
              ? <Spinner animation="border" size="sm" />
              : up
                ? <FaCheckCircle className="text-success" size={24} />
                : unknown
                  ? <FaServer className="text-secondary" size={24} />
                  : <FaTimesCircle className="text-danger" size={24} />
            }
          </div>
          <p className="small text-muted mb-3">{service.description}</p>
          <div className="d-flex gap-2 align-items-center">
            <Badge bg={up ? 'success' : unknown ? 'secondary' : 'danger'} className="text-uppercase">
              {checking ? 'checking…' : status}
            </Badge>
            {latency && <span className="small text-muted">{latency}ms</span>}
          </div>
        </Card.Body>
      </Card>
    </Col>
  );
}

function HealthCheckPage() {
  const [results, setResults] = useState({
    userService: { status: 'unknown', latency: null },
    appointmentService: { status: 'unknown', latency: null },
    reportService: { status: 'unknown', latency: null },
  });
  const [checking, setChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState(null);

  const runHealthChecks = async () => {
    setChecking(true);
    const updated = {};

    await Promise.all(
      SERVICES.map(async (svc) => {
        const start = Date.now();
        try {
          await svc.check();
          updated[svc.key] = { status: 'healthy', latency: Date.now() - start };
        } catch {
          updated[svc.key] = { status: 'unhealthy', latency: null };
        }
      })
    );

    setResults(updated);
    setLastChecked(new Date());
    setChecking(false);

    const allHealthy = Object.values(updated).every(r => r.status === 'healthy');
    if (allHealthy) toast.success('All services are healthy!');
    else toast.warning('Some services are down. Check details below.');
  };

  useEffect(() => {
    runHealthChecks();
  }, []);

  const healthy = Object.values(results).filter(r => r.status === 'healthy').length;
  const total = SERVICES.length;
  const allUp = healthy === total;

  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <h2 className="mb-0">
          <FaHeartbeat className="me-2 text-danger" />
          Service Health Monitor
        </h2>
        <Button variant="outline-primary" onClick={runHealthChecks} disabled={checking}>
          <FaSync className={`me-2 ${checking ? 'fa-spin' : ''}`} />
          {checking ? 'Checking…' : 'Refresh'}
        </Button>
      </div>

      {/* Overall Status Banner */}
      <Card className={`mb-4 shadow-sm text-white ${allUp ? 'bg-success' : 'bg-warning'}`} style={{ borderRadius: 12 }}>
        <Card.Body className="d-flex justify-content-between align-items-center py-3">
          <div className="d-flex align-items-center gap-3">
            {checking ? (
              <Spinner animation="border" size="sm" />
            ) : allUp ? (
              <FaCheckCircle size={28} />
            ) : (
              <FaTimesCircle size={28} />
            )}
            <div>
              <h5 className="mb-0">
                {checking ? 'Checking services…' : allUp ? 'All Systems Operational' : `${healthy}/${total} Services Healthy`}
              </h5>
              {lastChecked && (
                <small className={allUp ? 'text-white-50' : 'text-dark'}>
                  Last checked: {lastChecked.toLocaleTimeString()}
                </small>
              )}
            </div>
          </div>
          <Badge bg="light" text="dark" style={{ fontSize: '1rem', padding: '8px 16px' }}>
            {healthy}/{total} UP
          </Badge>
        </Card.Body>
      </Card>

      {/* Service Cards */}
      <Row>
        {SERVICES.map(svc => (
          <ServiceCard
            key={svc.key}
            service={svc}
            status={results[svc.key]?.status}
            latency={results[svc.key]?.latency}
            checking={checking}
          />
        ))}
      </Row>

      {/* Info Note */}
      <Card className="shadow-sm mt-2">
        <Card.Body className="small text-muted">
          <FaServer className="me-2" />
          Services run on <strong>localhost</strong> with Docker Compose. Make sure all containers are running
          before checking health status. User Service: :5001 | Appointment Service: :5002 | Report Service: :5003
        </Card.Body>
      </Card>
    </Container>
  );
}

export default HealthCheckPage;
