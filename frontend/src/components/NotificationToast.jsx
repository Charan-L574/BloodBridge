import React, { useEffect } from 'react';

const NotificationToast = ({ notification, onClose, index = 0 }) => {
  useEffect(() => {
    console.log('🎯 NotificationToast rendered with:', notification);
    console.log('   notification.data:', notification.data);
    console.log('   notification.notification_type:', notification.notification_type);
    
    // Play notification sound
    try {
      const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZUQ8NVanr8KJYEQ1Mm+Lxv3IkBjGH0fPTgjMGHm7A7+OZURANVaTs8KNYEBBNnOLyv3IlBzGH0vPTgzMGHm7B7+OZUQ8NVafr8KJYEAxMm+Hxv3MkBzGI0fPTgzQGHm7B7+OaUhANVafr8KJYEAxMm+Hxv3MkBzGI0fPTgzQGHm7B7+OaUhANVafr8KJYEA1Mm+Hxv3MlBzGI0fPTgzQGHm7B7+OaUhANVafr8KJYEA1Mm+Hxv3MlBzGI0fPUgzQGHm7B7+OaUhANVafr8KJZDw1Mm+HxvnUlBzGI0fPUgzQGHm7B7uOaUhAMVajr8KJZDw1Mm+HxvnUlBzGI0fPUgzQGHm/B7uOaUhAMVajr8KJZDw1Mm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDw1Mm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUhAMVajr8KJZDwxMm+HxvnUlBzGI0fPUgzMHHW/B7uOaUg==');
      audio.volume = 0.5;
      audio.play().catch(err => console.log('Audio play failed:', err));
    } catch (err) {
      console.log('Error playing notification sound:', err);
    }
    
    const timer = setTimeout(() => {
      onClose();
    }, 5000); // Auto-dismiss after 5 seconds

    return () => clearTimeout(timer);
  }, [onClose]);

  const getIcon = () => {
    switch (notification.notification_type) {
      case 'donor_response':
      case 'donor_accepted':
        return notification.data.is_eligible ? '✅' : '❌';
      case 'new_blood_request':
        return '🩸';
      case 'donation_confirmed':
        return '🎉';
      case 'request_fulfilled':
        return '✨';
      case 'request_urgent':
        return '🚨';
      case 'inventory_expiring':
        return '⚠️';
      default:
        return '🔔';
    }
  };

  const getColor = () => {
    switch (notification.notification_type) {
      case 'donor_response':
      case 'donor_accepted':
        return notification.data.is_eligible ? '#10b981' : '#f59e0b';
      case 'new_blood_request':
        return '#ef4444';
      case 'donation_confirmed':
        return '#8b5cf6';
      case 'request_fulfilled':
        return '#06b6d4';
      case 'request_urgent':
        return '#ef4444';
      case 'inventory_expiring':
        return '#f59e0b';
      default:
        return '#3b82f6';
    }
  };

  // Safe access to message
  const message = notification?.data?.message || notification?.message || 'New notification';
  console.log('📝 Toast message:', message);

  return (
    <div style={{
      position: 'fixed',
      top: `${20 + (index * 90)}px`,  // Stack toasts vertically
      right: '20px',
      backgroundColor: 'white',
      border: `2px solid ${getColor()}`,
      borderRadius: '8px',
      padding: '15px 20px',
      minWidth: '300px',
      maxWidth: '400px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      zIndex: 9999,
      animation: 'slideIn 0.3s ease-out'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
        <span style={{ fontSize: '24px' }}>{getIcon()}</span>
        <div style={{ flex: 1 }}>
          <h4 style={{ margin: 0, fontSize: '16px', color: '#1f2937' }}>
            {message}
          </h4>
          {notification.data.donor_name && (
            <p style={{ margin: '5px 0 0 0', fontSize: '14px', color: '#6b7280' }}>
              Blood Group: {notification.data.donor_blood_group}
              {notification.data.donor_phone && (
                <><br/>Phone: {notification.data.donor_phone}</>
              )}
            </p>
          )}
        </div>
        <button 
          onClick={onClose}
          style={{
            border: 'none',
            background: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            color: '#9ca3af',
            padding: 0
          }}
        >
          ×
        </button>
      </div>
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};

export default NotificationToast;
