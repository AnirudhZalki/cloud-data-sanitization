import React, { useState, useEffect } from 'react';

const BACKEND = 'http://localhost:8000';

/**
 * Derive a display-friendly filename for download links.
 */
function getFilename(label, isPdf, mimeType) {
  let ext = 'png';
  if (isPdf) ext = 'pdf';
  else if (mimeType) {
    const m = mimeType.match(/image\/(\w+)/);
    if (m) ext = m[1] === 'jpeg' ? 'jpg' : m[1];
  }
  return `${label.toLowerCase().replace(/\s+/g, '-')}.${ext}`;
}

/**
 * For PDFs served via S3 presigned URLs we route through the /proxy endpoint
 * so the backend re-serves the file with Content-Disposition: inline,
 * preventing the browser from forcing a download.
 * Local /files/... URLs already have inline headers from the backend.
 */
function toInlineUrl(url, isPdf) {
  if (!url) return url;
  // Already a local backend URL — no proxy needed
  if (url.startsWith(BACKEND)) return url;
  // S3 presigned or any external URL: proxy through backend for inline display
  if (isPdf) return `${BACKEND}/proxy?url=${encodeURIComponent(url)}`;
  return url;
}

/** ──────────────────────────────────────────────
 *  Inline file viewer — handles PDF and all image types
 *  ────────────────────────────────────────────── */
function FileViewer({ url, altText, isPdf, mimeType }) {
  const [status, setStatus] = useState('idle'); // 'idle' | 'loading' | 'ready' | 'error'
  const inlineUrl = toInlineUrl(url, isPdf);

  useEffect(() => {
    if (url) setStatus('loading');
    else setStatus('idle');
  }, [url]);

  if (!url || status === 'idle') {
    return (
      <div className="file-viewer-empty">
        <span className="viewer-icon">📄</span>
        <span>No preview available</span>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="file-viewer-empty">
        <span className="viewer-icon">⚠️</span>
        <span>Preview failed — <a href={inlineUrl} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>open in new tab</a></span>
      </div>
    );
  }

  if (isPdf) {
    return (
      /**
       * <object> is preferred over <iframe> for PDF embedding:
       * - It sends a proper Accept header, so servers know to serve PDF MIME
       * - Falls back gracefully to the inner link if the browser can't render inline
       */
      <object
        data={inlineUrl}
        type="application/pdf"
        className="file-viewer-frame"
        onLoad={() => setStatus('ready')}
        onError={() => setStatus('error')}
        aria-label={altText}
      >
        {/* Fallback message shown if inline PDF rendering is blocked */}
        <div className="file-viewer-empty">
          <span className="viewer-icon">📄</span>
          <span>
            Your browser can't display the PDF inline.{' '}
            <a href={inlineUrl} target="_blank" rel="noreferrer" style={{ color: '#60a5fa' }}>
              Open in new tab ↗
            </a>
          </span>
        </div>
      </object>
    );
  }

  // Image — supports jpg, png, webp, gif, avif, bmp, svg, etc.
  return (
    <img
      src={inlineUrl}
      alt={altText}
      className="file-viewer-img"
      onLoad={() => setStatus('ready')}
      onError={() => setStatus('error')}
    />
  );
}

/** ──────────────────────────────────────────────
 *  Single result card — viewer + download button
 *  ────────────────────────────────────────────── */
function ResultCard({ label, badge, badgeClass, url, isPdf, mimeType }) {
  const filename = getFilename(label, isPdf, mimeType);
  const inlineUrl = toInlineUrl(url, isPdf);

  return (
    <div className="result-card">
      {/* Header */}
      <div className="result-card-header">
        <div className="result-card-title">
          <h3>{label}</h3>
          <span className={`badge ${badgeClass}`}>{badge}</span>
        </div>

        {url && (
          /* Use an <a> with download attribute for downloading */
          <a
            href={inlineUrl}
            download={filename}
            className="btn btn-download"
            title={`Download ${label}`}
          >
            ⬇ Download
          </a>
        )}
      </div>

      {/* Viewer */}
      <div className="file-viewer-wrap">
        <FileViewer url={url} altText={label} isPdf={isPdf} mimeType={mimeType} />
      </div>
    </div>
  );
}

/** ──────────────────────────────────────────────
 *  Main exported component
 *  ────────────────────────────────────────────── */
export default function ResultViewer({
  originalUrl,
  sanitizedUrl,
  isAwsConnected,
  fileType,
  sensitiveData,
  extractedText,
  onReset,
}) {
  const isPdf = fileType === 'application/pdf';

  return (
    <div className="glass-card result-page" style={{ animation: 'fadeIn 0.5s ease-in' }}>
      {/* Top bar */}
      <div className="result-topbar">
        <h2>Sanitization Complete</h2>
        <button className="btn" onClick={onReset} style={{ margin: 0, padding: '0.5rem 1.25rem' }}>
          Upload Another
        </button>
      </div>

      {/* AWS warning */}
      {!isAwsConnected && (
        <div className="aws-warning">
          ⚠️ AWS S3 is not configured — previewing locally.
        </div>
      )}

      {/* Side-by-side viewers */}
      <div className="results-container">
        <ResultCard
          label="Original File"
          badge="Unsafe"
          badgeClass="original"
          url={originalUrl}
          isPdf={isPdf}
          mimeType={fileType}
        />
        <ResultCard
          label="Sanitized Output"
          badge="Secured"
          badgeClass=""
          url={sanitizedUrl}
          isPdf={isPdf}
          mimeType={fileType}
        />
      </div>

      {/* Metadata section */}
      <div className="result-meta">
        {sensitiveData && sensitiveData.length > 0 && (
          <div className="meta-block">
            <h3 className="meta-title danger">⚠️ Sensitive Data Detected</h3>
            <div className="sensitive-tags">
              {sensitiveData.map((item, i) => (
                <div key={i} className="sensitive-tag">
                  <strong>{item.type}:</strong> {item.text}
                </div>
              ))}
            </div>
          </div>
        )}

        {extractedText && (
          <div className="meta-block">
            <h3 className="meta-title">Extracted Text</h3>
            <div className="extracted-text-box">
              {extractedText}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
