import React, { useState, useEffect, useRef } from 'react';
import {
  Container, Row, Col, Card, Table, Badge, Button, Spinner, Alert, Modal, Form, ProgressBar
} from 'react-bootstrap';
import { toast } from 'react-toastify';
import {
  FaFileAlt, FaUpload, FaDownload, FaTrash, FaPlus, FaFilePdf, FaFileImage, FaFile
} from 'react-icons/fa';
import { reportAPI } from '../services/api';

const FILE_ICONS = {
  pdf: <FaFilePdf className="text-danger" />,
  jpg: <FaFileImage className="text-success" />,
  jpeg: <FaFileImage className="text-success" />,
  png: <FaFileImage className="text-info" />,
};

function getFileIcon(type) {
  return FILE_ICONS[type?.toLowerCase()] || <FaFile className="text-secondary" />;
}

function formatSize(bytes) {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [uploadForm, setUploadForm] = useState({ file: null, description: '', is_public: false });
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const res = await reportAPI.getReports();
      setReports(res.data.reports || []);
    } catch {
      setError('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setUploadForm(prev => ({ ...prev, file }));
      setShowUpload(true);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) setUploadForm(prev => ({ ...prev, file }));
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadForm.file) { toast.error('Please select a file'); return; }

    const formData = new FormData();
    formData.append('file', uploadForm.file);
    formData.append('description', uploadForm.description);
    formData.append('is_public', uploadForm.is_public ? 'true' : 'false');

    setUploading(true);
    setUploadProgress(0);

    // Simulate progress
    const interval = setInterval(() => {
      setUploadProgress(p => (p < 85 ? p + 10 : p));
    }, 200);

    try {
      await reportAPI.uploadReport(formData);
      clearInterval(interval);
      setUploadProgress(100);
      toast.success('Report uploaded successfully!');
      setShowUpload(false);
      setUploadForm({ file: null, description: '', is_public: false });
      fetchReports();
    } catch (err) {
      clearInterval(interval);
      toast.error(err.response?.data?.message || 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDownload = async (reportId, fileName) => {
    try {
      const res = await reportAPI.downloadReport(reportId);
      const url = res.data.download_url;
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.target = '_blank';
      a.click();
      toast.success('Download started');
    } catch {
      toast.error('Failed to generate download link');
    }
  };

  const handleDelete = async (reportId) => {
    if (!window.confirm('Delete this report? This cannot be undone.')) return;
    try {
      await reportAPI.deleteReport(reportId);
      toast.success('Report deleted');
      fetchReports();
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to delete');
    }
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" />
        <p className="mt-2 text-muted">Loading reports…</p>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
        <h2 className="mb-0">
          <FaFileAlt className="me-2 text-primary" />
          Medical Reports
        </h2>
        <Button variant="primary" onClick={() => setShowUpload(true)}>
          <FaPlus className="me-2" />Upload Report
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      {/* Drag & Drop Zone */}
      <div
        className={`mb-4 p-5 text-center border border-2 rounded-3 ${dragOver ? 'border-primary bg-primary bg-opacity-10' : 'border-dashed'}`}
        style={{ borderStyle: 'dashed', cursor: 'pointer', transition: 'all 0.3s' }}
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <FaUpload size={40} className={`mb-3 ${dragOver ? 'text-primary' : 'text-muted'}`} />
        <h5 className={dragOver ? 'text-primary' : 'text-muted'}>
          {dragOver ? 'Drop file here' : 'Drag & drop a file, or click to browse'}
        </h5>
        <p className="small text-muted mb-0">Supports PDF, JPG, PNG, DOC files</p>
        <input ref={fileInputRef} type="file" className="d-none" onChange={handleFileSelect} accept=".pdf,.jpg,.jpeg,.png,.doc,.docx" />
      </div>

      {/* Reports Table */}
      <Card className="shadow-sm">
        <Card.Body className="p-0">
          {reports.length === 0 ? (
            <div className="empty-state py-5">
              <div className="empty-state-icon"><FaFileAlt /></div>
              <h5>No reports yet</h5>
              <p>Upload your first medical report to get started</p>
              <Button variant="primary" onClick={() => setShowUpload(true)}>
                <FaUpload className="me-2" />Upload Report
              </Button>
            </div>
          ) : (
            <div className="table-responsive">
              <Table hover className="mb-0 align-middle">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>File</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Description</th>
                    <th>Visibility</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r, idx) => (
                    <tr key={r.id}>
                      <td className="text-muted small">{idx + 1}</td>
                      <td>
                        <span className="me-2">{getFileIcon(r.file_type)}</span>
                        <span className="fw-semibold small">{r.file_name}</span>
                      </td>
                      <td>
                        <Badge bg="secondary" className="text-uppercase">{r.file_type || '—'}</Badge>
                      </td>
                      <td className="small">{formatSize(r.file_size)}</td>
                      <td className="small text-muted" style={{ maxWidth: 180 }}>
                        {r.description || <span className="text-muted">—</span>}
                      </td>
                      <td>
                        <Badge bg={r.is_public ? 'success' : 'secondary'}>
                          {r.is_public ? 'Public' : 'Private'}
                        </Badge>
                      </td>
                      <td className="small text-muted">
                        {r.uploaded_at ? new Date(r.uploaded_at).toLocaleDateString() : '—'}
                      </td>
                      <td>
                        <div className="d-flex gap-1">
                          <Button
                            size="sm" variant="outline-primary"
                            onClick={() => handleDownload(r.id, r.file_name)}
                            title="Download"
                          >
                            <FaDownload />
                          </Button>
                          <Button
                            size="sm" variant="outline-danger"
                            onClick={() => handleDelete(r.id)}
                            title="Delete"
                          >
                            <FaTrash />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Upload Modal */}
      <Modal show={showUpload} onHide={() => !uploading && setShowUpload(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title><FaUpload className="me-2" />Upload Medical Report</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleUpload}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>File <span className="text-danger">*</span></Form.Label>
              <Form.Control
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
                onChange={handleFileSelect}
                required={!uploadForm.file}
              />
              {uploadForm.file && (
                <div className="mt-2 small text-success">
                  Selected: {uploadForm.file.name} ({formatSize(uploadForm.file.size)})
                </div>
              )}
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea" rows={2}
                placeholder="Brief description (e.g., Blood test results Jan 2025)"
                value={uploadForm.description}
                onChange={e => setUploadForm(prev => ({ ...prev, description: e.target.value }))}
              />
            </Form.Group>

            <Form.Check
              type="switch"
              label="Share with doctors (public)"
              checked={uploadForm.is_public}
              onChange={e => setUploadForm(prev => ({ ...prev, is_public: e.target.checked }))}
            />

            {uploading && (
              <ProgressBar animated now={uploadProgress} label={`${uploadProgress}%`} className="mt-3" />
            )}
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowUpload(false)} disabled={uploading}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={uploading}>
              {uploading
                ? <><Spinner as="span" animation="border" size="sm" className="me-2" />Uploading…</>
                : <><FaUpload className="me-2" />Upload</>
              }
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
}

export default ReportsPage;
