import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    const result = await login(email, password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };
  
  return (
    <div className="container" style={{ maxWidth: '400px', margin: '80px auto 0', padding: '0 20px' }}>
      <div className="card">
        <h2 style={{ marginBottom: '20px', textAlign: 'center', color: '#dc2626' }}>
          🩸 BloodBridge
        </h2>
        
        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
            />
          </div>
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%' }}
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        <p style={{ marginTop: '20px', textAlign: 'center', color: '#6b7280' }}>
          Don't have an account?{' '}
          <a href="/register" style={{ color: '#dc2626', fontWeight: '500' }}>
            Register
          </a>
        </p>
        
        <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f3f4f6', borderRadius: '4px' }}>
          <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '8px' }}>
            <strong>Demo Credentials:</strong>
          </p>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: '4px 0' }}>
            Donor: donor1@example.com / password123
          </p>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: '4px 0' }}>
            Requester: requester@example.com / password123
          </p>
          <p style={{ fontSize: '12px', color: '#6b7280', margin: '4px 0' }}>
            Hospital: hospital1@example.com / password123
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
