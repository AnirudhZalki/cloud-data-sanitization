import React, { useState, useRef, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function FileUpload({ onUploadSuccess }) {
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const { token } = useContext(AuthContext);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) handleFiles(e.dataTransfer.files[0]);
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files?.[0]) handleFiles(e.target.files[0]);
  };

  const handleFiles = async (file) => {
    if (!file.type.startsWith('image/') && file.type !== 'application/pdf') {
      setError('Only images and PDFs are supported');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to upload');
      }

      const data = await response.json();

      onUploadSuccess({
        originalUrl: data.original_url,
        sanitizedUrl: data.sanitized_url,
        isAwsConnected: data.is_aws_connected,
        fileType: file.type,
        sensitiveData: data.sensitive_data,
        extractedText: data.extracted_text,
      });

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onButtonClick = () => inputRef.current.click();

  if (loading) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: '3rem' }}>
        <h2 style={{ marginBottom: '0.5rem' }}>Processing File…</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Detecting and redacting sensitive data — this may take a moment.
        </p>
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="glass-card">
      <div
        className={`upload-zone ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={onButtonClick}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*, application/pdf"
          onChange={handleChange}
          style={{ display: 'none' }}
        />
        <div className="upload-icon">☁️</div>
        <div className="upload-text">Drag &amp; Drop your file here</div>
        <div className="upload-subtext">Supports PNG, JPG, JPEG, PDF</div>
        <button className="btn" onClick={(e) => { e.stopPropagation(); onButtonClick(); }}>
          Browse Files
        </button>
      </div>

      {error && (
        <div style={{ color: 'var(--error)', marginTop: '1rem', textAlign: 'center' }}>
          Error: {error}
        </div>
      )}
    </div>
  );
}
