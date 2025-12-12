import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { authAPI } from '../services/api';

const Navbar = () => {
  const { user, isAuthenticated, logout, setToken, loadUser } = useAuthStore();
  const navigate = useNavigate();
  const [switching, setSwitching] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  
  // Load unread count
  useEffect(() => {
    if (isAuthenticated) {
      loadUnreadCount();
      // Refresh every 30 seconds
      const interval = setInterval(loadUnreadCount, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated]);
  
  const loadUnreadCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/notifications/unread-count', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setUnreadCount(data.unread_count);
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  };
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  const handleRoleSwitch = async () => {
    if (!['donor', 'requester'].includes(user?.role)) {
      alert('Only donors and requesters can switch roles');
      return;
    }
    
    const newRole = user.role === 'donor' ? 'requester' : 'donor';
    
    // Check if switching to donor and missing required fields
    if (newRole === 'donor') {
      if (!user.blood_group || !user.age || !user.weight) {
        const missingFields = [];
        if (!user.blood_group) missingFields.push('Blood Group');
        if (!user.age) missingFields.push('Age');
        if (!user.weight) missingFields.push('Weight');
        
        const goToProfile = window.confirm(
          `To become a donor, you need to update your profile with:\n\n${missingFields.join('\n')}\n\nGo to Edit Profile now?`
        );
        
        if (goToProfile) {
          navigate('/profile');
        }
        return;
      }
    }
    
    const confirmed = window.confirm(
      `Switch role from ${user.role} to ${newRole}?\n\nYou will be able to switch back anytime.`
    );
    
    if (!confirmed) return;
    
    setSwitching(true);
    try {
      const response = await authAPI.switchRole(newRole);
      
      // Update token and reload user
      setToken(response.data.access_token);
      await loadUser();
      
      alert(`✅ Role switched to ${newRole}!`);
      window.location.href = '/dashboard'; // Force page reload
    } catch (error) {
      console.error('Role switch error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
      
      // If error is about missing profile info, redirect to profile
      if (errorMsg.includes('required')) {
        const goToProfile = window.confirm(
          `Error: ${errorMsg}\n\nGo to Edit Profile to update your information?`
        );
        if (goToProfile) {
          navigate('/profile');
        }
      } else {
        alert('Error switching role: ' + errorMsg);
      }
    } finally {
      setSwitching(false);
    }
  };
  
  if (!isAuthenticated) {
    return null;
  }
  
  return (
    <nav className="navbar">
      <div className="navbar-content">
        <h1 style={{ textAlign: 'center', width: '100%', marginBottom: '15px' }}>🩸 BloodBridge</h1>
      </div>
      <div className="navbar-menu" style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '30px', 
        alignItems: 'center',
        flexWrap: 'wrap',
        padding: '10px 20px'
      }}>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/map">🗺️ Map</Link>
        {user?.role === 'donor' && (
          <>
            <Link to="/quick-stats">Activity Insights</Link>
            <Link to="/donation-history">Donation History</Link>
          </>
        )}
        {user?.role === 'requester' && (
          <>
            <Link to="/quick-stats">Activity Insights</Link>
            <Link to="/donation-history">Donation History</Link>
          </>
        )}
        {user?.role === 'hospital' && (
          <>
            <Link to="/demand-forecast">Blood Demand Forecast</Link>
            <Link to="/donation-history">Donation History</Link>
          </>
        )}
        <Link to="/notifications" style={{ position: 'relative' }}>
          🔔 Notifications
          {unreadCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '-8px',
              right: '-8px',
              backgroundColor: '#ef4444',
              color: 'white',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '11px',
              fontWeight: 'bold'
            }}>
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </Link>
        <Link to="/profile">Edit Profile</Link>
        <span style={{ color: '#fca5a5' }}>
          {user?.full_name} ({user?.role})
        </span>
        {['donor', 'requester'].includes(user?.role) && (
          <button 
              onClick={handleRoleSwitch}
              disabled={switching}
              style={{ 
                background: '#10b981', 
                border: 'none',
                color: 'white',
                padding: '5px 15px',
                borderRadius: '4px',
                cursor: switching ? 'not-allowed' : 'pointer',
                marginRight: '10px'
              }}
            >
              {switching ? 'Switching...' : `Switch to ${user?.role === 'donor' ? 'Requester' : 'Donor'}`}
            </button>
          )}
          <button 
            onClick={handleLogout}
            style={{ 
              background: 'transparent', 
              border: '1px solid white',
              color: 'white',
              padding: '5px 15px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
      </div>
    </nav>
  );
};

export default Navbar;
