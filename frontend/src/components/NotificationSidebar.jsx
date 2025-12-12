import React, { useState, useEffect } from 'react';
import { notificationAPI } from '../services/api';

const NotificationSidebar = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await notificationAPI.getNotifications();
      // Show only recent 5 notifications
      setNotifications(response.data.slice(0, 5));
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await notificationAPI.markAsRead(id);
      loadNotifications(); // Reload
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  const deleteNotification = async (id) => {
    try {
      await notificationAPI.deleteNotification(id);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  if (loading) {
    return (
      <div className="card" style={styles.sidebar}>
        <h3 style={styles.title}>Notifications</h3>
        <p style={styles.loading}>Loading...</p>
      </div>
    );
  }

  return (
    <div className="card" style={styles.sidebar}>
      <h3 style={styles.title}>Notifications</h3>
      {notifications.length === 0 ? (
        <p style={styles.empty}>No notifications</p>
      ) : (
        <div style={styles.list}>
          {notifications.map(notif => (
            <div 
              key={notif.id} 
              style={{
                ...styles.item,
                backgroundColor: notif.is_read ? '#f9fafb' : '#fef3c7'
              }}
            >
              <div style={styles.content}>
                <p style={styles.message}>{notif.message}</p>
                <span style={styles.time}>
                  {new Date(notif.created_at).toLocaleTimeString()}
                </span>
              </div>
              <div style={styles.actions}>
                {!notif.is_read && (
                  <button
                    onClick={() => markAsRead(notif.id)}
                    style={styles.readBtn}
                    title="Mark as read"
                  >
                    ✓
                  </button>
                )}
                <button
                  onClick={() => deleteNotification(notif.id)}
                  style={styles.deleteBtn}
                  title="Delete"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  sidebar: {
    width: '300px',
    padding: '20px',
    margin: '0'
  },
  title: {
    fontSize: '18px',
    fontWeight: '600',
    marginBottom: '20px',
    color: '#111827',
    borderBottom: '2px solid #ef4444',
    paddingBottom: '10px',
    textAlign: 'center'
  },
  loading: {
    textAlign: 'center',
    color: '#6b7280',
    fontSize: '14px'
  },
  empty: {
    textAlign: 'center',
    color: '#9ca3af',
    fontSize: '14px',
    marginTop: '20px'
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px'
  },
  item: {
    padding: '15px',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'start',
    gap: '12px'
  },
  content: {
    flex: 1,
    minWidth: 0
  },
  message: {
    fontSize: '13px',
    margin: '0 0 4px 0',
    color: '#374151',
    lineHeight: '1.4',
    wordWrap: 'break-word'
  },
  time: {
    fontSize: '11px',
    color: '#9ca3af'
  },
  actions: {
    display: 'flex',
    gap: '8px'
  },
  readBtn: {
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    width: '24px',
    height: '24px',
    cursor: 'pointer',
    fontSize: '14px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 0
  },
  deleteBtn: {
    backgroundColor: '#ef4444',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    width: '24px',
    height: '24px',
    cursor: 'pointer',
    fontSize: '18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 0,
    lineHeight: '1'
  }
};

export default NotificationSidebar;
