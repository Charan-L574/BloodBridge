import React, { useState, useEffect } from 'react';
import { createWebSocket } from '../services/api';
import useAuthStore from '../store/authStore';
import axios from 'axios';

const Notifications = () => {
  const { user, token } = useAuthStore();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  useEffect(() => {
    loadNotifications();
    loadUnreadCount();
    
    // Setup WebSocket for real-time notifications
    let websocket;
    if (token) {
      try {
        websocket = createWebSocket(token);
        
        websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          // Reload notifications when new one arrives
          if (message.type === 'notification') {
            console.log('🔔 New notification received, reloading...');
            loadNotifications();
            loadUnreadCount();
          }
        };
        
        websocket.onerror = (error) => {
          console.error('WebSocket error in Notifications:', error);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
      }
    }
    
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [token, showUnreadOnly]);

  const loadNotifications = async () => {
    try {
      console.log('📥 Fetching notifications from backend...');
      const response = await axios.get(
        `http://localhost:8000/notifications${showUnreadOnly ? '?unread_only=true' : ''}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      console.log('✅ Notifications fetched:', response.data);
      setNotifications(response.data);
    } catch (error) {
      console.error('❌ Error loading notifications:', error);
      console.error('Error details:', error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const loadUnreadCount = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/notifications/unread-count',
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error loading unread count:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(
        `http://localhost:8000/notifications/${notificationId}/read`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      loadNotifications();
      loadUnreadCount();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await axios.put(
        'http://localhost:8000/notifications/mark-all-read',
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      loadNotifications();
      loadUnreadCount();
      alert('✅ All notifications marked as read');
    } catch (error) {
      console.error('Error marking all as read:', error);
      alert('Error: ' + (error.response?.data?.detail || 'Failed to mark notifications as read'));
    }
  };

  const deleteNotification = async (notificationId) => {
    if (!window.confirm('Delete this notification?')) return;
    
    try {
      await axios.delete(
        `http://localhost:8000/notifications/${notificationId}`,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      loadNotifications();
      loadUnreadCount();
    } catch (error) {
      console.error('Error deleting notification:', error);
      alert('Error: ' + (error.response?.data?.detail || 'Failed to delete notification'));
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'new_blood_request':
        return '🩸';
      case 'donor_accepted':
        return '✅';
      case 'donation_confirmed':
        return '🎉';
      case 'request_fulfilled':
        return '✨';
      case 'donor_ineligible':
        return '⚠️';
      default:
        return '🔔';
    }
  };

  const getColor = (type) => {
    switch (type) {
      case 'new_blood_request':
        return '#ef4444';
      case 'donor_accepted':
        return '#10b981';
      case 'donation_confirmed':
        return '#8b5cf6';
      case 'request_fulfilled':
        return '#06b6d4';
      case 'donor_ineligible':
        return '#f59e0b';
      default:
        return '#6b7280';
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  console.log('📊 Notifications component state:', { loading, notifications: notifications.length, unreadCount, showUnreadOnly });

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', color: '#6b7280' }}>
        Loading notifications...
      </div>
    );
  }

  console.log('✅ Notifications component rendering with', notifications.length, 'notifications');

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0 }}>
          🔔 Notifications ({notifications.length}) {unreadCount > 0 && (
            <span style={{
              backgroundColor: '#ef4444',
              color: 'white',
              borderRadius: '12px',
              padding: '2px 8px',
              fontSize: '12px',
              marginLeft: '8px'
            }}>
              {unreadCount}
            </span>
          )}
        </h3>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => setShowUnreadOnly(!showUnreadOnly)}
            className="btn"
            style={{ padding: '6px 12px', fontSize: '14px' }}
          >
            {showUnreadOnly ? 'Show All' : 'Unread Only'}
          </button>
          {unreadCount > 0 && (
            <button
              onClick={markAllAsRead}
              className="btn btn-success"
              style={{ padding: '6px 12px', fontSize: '14px' }}
            >
              Mark All Read
            </button>
          )}
        </div>
      </div>

      {notifications.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
          <div style={{ fontSize: '48px', marginBottom: '10px' }}>🔕</div>
          <p>No {showUnreadOnly ? 'unread ' : ''}notifications</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {notifications.map(notification => (
            <div
              key={notification.id}
              style={{
                padding: '15px',
                border: `2px solid ${notification.is_read ? '#e5e7eb' : getColor(notification.notification_type)}`,
                borderRadius: '8px',
                backgroundColor: notification.is_read ? '#f9fafb' : 'white',
                display: 'flex',
                gap: '15px',
                alignItems: 'start'
              }}
            >
              <div style={{ fontSize: '32px', flexShrink: 0 }}>
                {getIcon(notification.notification_type)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '5px' }}>
                  <h4 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>
                    {notification.title}
                  </h4>
                  <span style={{ fontSize: '12px', color: '#6b7280', whiteSpace: 'nowrap', marginLeft: '10px' }}>
                    {formatDate(notification.created_at)}
                  </span>
                </div>
                <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#4b5563' }}>
                  {notification.message}
                </p>
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                  {!notification.is_read && (
                    <button
                      onClick={() => markAsRead(notification.id)}
                      className="btn"
                      style={{
                        padding: '4px 12px',
                        fontSize: '12px',
                        backgroundColor: '#10b981',
                        color: 'white'
                      }}
                    >
                      Mark as Read
                    </button>
                  )}
                  <button
                    onClick={() => deleteNotification(notification.id)}
                    className="btn"
                    style={{
                      padding: '4px 12px',
                      fontSize: '12px',
                      backgroundColor: '#ef4444',
                      color: 'white'
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Notifications;
