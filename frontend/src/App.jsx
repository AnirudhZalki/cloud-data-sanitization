import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useContext, useState } from 'react';
import { AuthContext, AuthProvider } from './context/AuthContext';
import FileUpload from './components/FileUpload';
import ResultViewer from './components/ResultViewer';
import Login from './components/Login';
import Register from './components/Register';
import AdminDashboard from './components/AdminDashboard';

function ProtectedRoute({ children, reqAdmin = false }) {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (reqAdmin && user.role !== 'admin') return <Navigate to="/" replace />;
  return children;
}

function MainApp() {
  const [result, setResult] = useState(null);
  const { user, logout } = useContext(AuthContext);

  const handleUploadSuccess = (data) => setResult(data);
  const handleReset = () => setResult(null);

  return (
    <div className="app-container">
      <header className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Link to="/" style={{ textDecoration: 'none', color: 'currentcolor' }}>
            <h1>Cloud Data Sanitizer</h1>
          </Link>
          <p>Intelligent PII Redaction & Privacy Compliance using Computer Vision</p>
        </div>
        {user && (
          <div style={{ textAlign: 'right' }}>
            <p>Welcome, <strong>{user.username}</strong> ({user.role})</p>
            <div style={{ marginTop: '0.5rem' }}>
              {user.role === 'admin' && (
                <Link to="/admin" style={{ color: 'var(--primary)', marginRight: '1rem', textDecoration: 'none' }}>Admin Dashboard</Link>
              )}
              <button onClick={logout} className="btn" style={{ padding: '0.4rem 1rem', fontSize: '0.9rem' }}>Logout</button>
            </div>
          </div>
        )}
      </header>

      <main>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin" element={
            <ProtectedRoute reqAdmin={true}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
          <Route path="/" element={
            <ProtectedRoute>
              {!result ? (
                <FileUpload onUploadSuccess={handleUploadSuccess} />
              ) : (
                <ResultViewer
                  originalUrl={result.originalUrl}
                  sanitizedUrl={result.sanitizedUrl}
                  isAwsConnected={result.isAwsConnected}
                  sensitiveData={result.sensitiveData}
                  extractedText={result.extractedText}
                  fileType={result.fileType}
                  onReset={handleReset}
                />
              )}
            </ProtectedRoute>
          } />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <MainApp />
      </Router>
    </AuthProvider>
  );
}

export default App;
