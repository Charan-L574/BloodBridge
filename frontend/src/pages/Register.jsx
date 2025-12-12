import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const ROLES = ['donor', 'requester', 'hospital'];

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    role: 'donor',
    blood_group: '',
    age: '',
    weight: '',
    visibility_mode: 'both',
    hospital_name: '',
    hospital_address: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    // Prepare data based on role
    const data = { ...formData };
    if (formData.role === 'donor') {
      data.age = parseInt(formData.age);
      data.weight = parseFloat(formData.weight);
    } else {
      delete data.blood_group;
      delete data.age;
      delete data.weight;
      delete data.visibility_mode;
    }
    
    if (formData.role !== 'hospital') {
      delete data.hospital_name;
      delete data.hospital_address;
    }
    
    const result = await register(data);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };
  
  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  return (
    <div className="container" style={{ maxWidth: '500px', marginTop: '40px' }}>
      <div className="card">
        <h2 style={{ marginBottom: '20px', textAlign: 'center', color: '#dc2626' }}>
          Register
        </h2>
        
        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email *</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Password *</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Full Name *</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Phone *</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>
          
          <div className="form-group">
            <label>Role *</label>
            <select name="role" value={formData.role} onChange={handleChange} required>
              {ROLES.map(role => (
                <option key={role} value={role}>
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </option>
              ))}
            </select>
          </div>
          
          {formData.role === 'donor' && (
            <>
              <div className="form-group">
                <label>Blood Group *</label>
                <select name="blood_group" value={formData.blood_group} onChange={handleChange} required>
                  <option value="">Select Blood Group</option>
                  {BLOOD_GROUPS.map(group => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-2">
                <div className="form-group">
                  <label>Age *</label>
                  <input
                    type="number"
                    name="age"
                    value={formData.age}
                    onChange={handleChange}
                    required
                    min="18"
                    max="65"
                  />
                </div>
                
                <div className="form-group">
                  <label>Weight (kg) *</label>
                  <input
                    type="number"
                    name="weight"
                    value={formData.weight}
                    onChange={handleChange}
                    required
                    min="50"
                    step="0.1"
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Location Visibility</label>
                <select name="visibility_mode" value={formData.visibility_mode} onChange={handleChange}>
                  <option value="saved_only">Saved Locations Only</option>
                  <option value="live_only">Live Location Only</option>
                  <option value="both">Both</option>
                </select>
              </div>
            </>
          )}
          
          {formData.role === 'hospital' && (
            <>
              <div className="form-group">
                <label>Hospital Name *</label>
                <input
                  type="text"
                  name="hospital_name"
                  value={formData.hospital_name}
                  onChange={handleChange}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Hospital Address *</label>
                <textarea
                  name="hospital_address"
                  value={formData.hospital_address}
                  onChange={handleChange}
                  required
                  rows="3"
                />
              </div>
            </>
          )}
          
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%' }}
            disabled={loading}
          >
            {loading ? 'Registering...' : 'Register'}
          </button>
        </form>
        
        <p style={{ marginTop: '20px', textAlign: 'center', color: '#6b7280' }}>
          Already have an account?{' '}
          <a href="/login" style={{ color: '#dc2626', fontWeight: '500' }}>
            Login
          </a>
        </p>
      </div>
    </div>
  );
};

export default Register;
