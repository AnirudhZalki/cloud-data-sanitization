import React, { useEffect, useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function AdminDashboard() {
  const { token, user } = useContext(AuthContext);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/history', {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => {
      if (!res.ok) throw new Error('Failed to fetch history');
      return res.json();
    })
    .then(data => setHistory(data))
    .catch(err => setError(err.message))
    .finally(() => setLoading(false));
  }, [token]);

  if (user?.role !== 'admin') {
    return <div style={{ color: 'var(--error)' }}>Access Denied. Admins only.</div>;
  }

  if (loading) return <div>Loading history...</div>;
  if (error) return <div style={{ color: 'var(--error)' }}>{error}</div>;

  return (
    <div className="glass-card" style={{ maxWidth: '800px', margin: '2rem auto', padding: '2rem' }}>
      <h2>Admin Dashboard - Sanitization History</h2>
      {history.length === 0 ? (
        <p>No processed files found.</p>
      ) : (
        <div style={{ overflowX: 'auto', marginTop: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.2)' }}>
                <th style={{ padding: '0.8rem' }}>File Name</th>
                <th style={{ padding: '0.8rem' }}>Date</th>
                <th style={{ padding: '0.8rem' }}>Format</th>
                <th style={{ padding: '0.8rem' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {history.map(record => (
                <tr key={record.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                  <td style={{ padding: '0.8rem' }}>{record.original_filename}</td>
                  <td style={{ padding: '0.8rem' }}>{new Date(record.created_at).toLocaleString()}</td>
                  <td style={{ padding: '0.8rem' }}>{record.file_type}</td>
                  <td style={{ padding: '0.8rem' }}>
                    <a href={record.sanitized_url} target="_blank" rel="noreferrer" style={{ color: 'var(--primary)', marginRight: '1rem' }}>View Sanitized</a>
                    <a href={record.original_url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-secondary)' }}>View Original</a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
