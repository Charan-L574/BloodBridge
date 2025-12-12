import React, { useState, useEffect } from 'react';
import { Link, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import NotificationToast from '../components/NotificationToast';
import Notifications from '../components/Notifications';
import { bloodRequestAPI, createWebSocket } from '../services/api';

// Import tab components
import RequesterMainDashboard from './requester/RequesterMainDashboard';
import RequesterDemandForecast from './requester/RequesterDemandForecast';
import RequesterDonationHistory from './requester/RequesterDonationHistory';

const RequesterDashboard = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const token = useAuthStore(state => state.token);

  useEffect(() => {
    // Setup WebSocket
    if (token) {
      console.log('🔌 Connecting RequesterDashboard to WebSocket...');
      const websocket = createWebSocket(token);
      
      websocket.onopen = () => {
        console.log('✅ RequesterDashboard WebSocket connected');
      };
      
      websocket.onerror = (error) => {
        console.error('❌ RequesterDashboard WebSocket error:', error);
      };
      
      websocket.onclose = () => {
        console.log('🔌 RequesterDashboard WebSocket closed');
      };
      
      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        
        if (message.type === 'notification') {
          console.log('🔔 RequesterDashboard notification:', message);
          setNotifications(prev => {
            const newNotifications = [...prev, { ...message, id: Date.now() }];
            console.log('📋 Updated notifications array:', newNotifications);
            return newNotifications;
          });
        }
      };

      return () => websocket.close();
    }
  }, [token]);

  // Load unread notification count
  useEffect(() => {
    const loadUnreadCount = async () => {
      try {
        const response = await bloodRequestAPI.getUnreadNotificationCount();
        setUnreadCount(response.data.unread_count);
      } catch (error) {
        console.error('Error loading unread count:', error);
      }
    };
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const handleRemoveToast = (index) => {
    setNotifications(prev => prev.filter((_, i) => i !== index));
  };

  const isActive = (path) => location.pathname === path || (path === '/requester-dashboard' && location.pathname === '/requester-dashboard');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      {/* Left Sidebar Navigation */}
      <div style={{
        width: '250px',
        backgroundColor: '#fff',
        borderRight: '1px solid #e0e0e0',
        padding: '20px',
        boxShadow: '2px 0 5px rgba(0,0,0,0.05)'
      }}>
        <div style={{ marginBottom: '30px' }}>
          <h2 style={{ margin: 0, color: '#d32f2f', fontSize: '22px' }}>BloodBridge</h2>
          <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '12px' }}>Requester Portal</p>
        </div>

        <nav>
          <Link 
            to="/requester-dashboard"
            style={{
              display: 'block',
              padding: '12px 15px',
              marginBottom: '8px',
              textDecoration: 'none',
              color: isActive('/requester-dashboard') ? '#fff' : '#333',
              backgroundColor: isActive('/requester-dashboard') ? '#d32f2f' : 'transparent',
              borderRadius: '8px',
              transition: 'all 0.3s',
              fontWeight: isActive('/requester-dashboard') ? 'bold' : 'normal'
            }}
          >
            🏠 Dashboard
          </Link>

          <Link 
            to="/requester-dashboard/demand-forecast"
            style={{
              display: 'block',
              padding: '12px 15px',
              marginBottom: '8px',
              textDecoration: 'none',
              color: isActive('/requester-dashboard/demand-forecast') ? '#fff' : '#333',
              backgroundColor: isActive('/requester-dashboard/demand-forecast') ? '#d32f2f' : 'transparent',
              borderRadius: '8px',
              transition: 'all 0.3s',
              fontWeight: isActive('/requester-dashboard/demand-forecast') ? 'bold' : 'normal'
            }}
          >
            📊 Demand Forecast
          </Link>

          <Link 
            to="/requester-dashboard/donation-history"
            style={{
              display: 'block',
              padding: '12px 15px',
              marginBottom: '8px',
              textDecoration: 'none',
              color: isActive('/requester-dashboard/donation-history') ? '#fff' : '#333',
              backgroundColor: isActive('/requester-dashboard/donation-history') ? '#d32f2f' : 'transparent',
              borderRadius: '8px',
              transition: 'all 0.3s',
              fontWeight: isActive('/requester-dashboard/donation-history') ? 'bold' : 'normal'
            }}
          >
            📜 Donation History
          </Link>

          <div style={{ 
            marginTop: '30px', 
            paddingTop: '20px',
            borderTop: '1px solid #e0e0e0'
          }}>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              style={{
                width: '100%',
                padding: '12px',
                backgroundColor: '#fff',
                color: '#d32f2f',
                border: '2px solid #d32f2f',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 'bold',
                transition: 'all 0.3s'
              }}
              onMouseOver={(e) => {
                e.target.style.backgroundColor = '#d32f2f';
                e.target.style.color = '#fff';
              }}
              onMouseOut={(e) => {
                e.target.style.backgroundColor = '#fff';
                e.target.style.color = '#d32f2f';
              }}
            >
              🚪 Logout
            </button>
          </div>
        </nav>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex' }}>
        <div style={{ flex: 1, padding: '30px', overflowY: 'auto' }}>
          <Routes>
            <Route path="/" element={<RequesterMainDashboard />} />
            <Route path="/demand-forecast" element={<RequesterDemandForecast />} />
            <Route path="/donation-history" element={<RequesterDonationHistory />} />
          </Routes>
        </div>

        {/* Right Sidebar - Notifications */}
        <div style={{
          width: '300px',
          backgroundColor: '#fff',
          borderLeft: '1px solid #e0e0e0',
          padding: '20px',
          overflowY: 'auto',
          boxShadow: '-2px 0 5px rgba(0,0,0,0.05)'
        }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: '15px'
          }}>
            <h3 style={{ margin: 0, fontSize: '18px', color: '#333' }}>🔔 Notifications</h3>
            {unreadCount > 0 && (
              <span style={{
                backgroundColor: '#d32f2f',
                color: 'white',
                borderRadius: '12px',
                padding: '2px 8px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {unreadCount}
              </span>
            )}
          </div>
          <Notifications compact={true} />
        </div>
      </div>

      {/* Toast Notifications */}
      {console.log('🎨 Rendering toasts, notifications array:', notifications)}
      {notifications.map((notif, index) => {
        console.log(`🎨 Rendering toast ${index}:`, notif);
        return (
          <NotificationToast
            key={notif.id || index}
            notification={notif}
            index={index}
            onClose={() => handleRemoveToast(index)}
          />
        );
      })}
    </div>
  );
};

export default RequesterDashboard;
