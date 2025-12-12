import React, { useState, useEffect } from 'react';
import { bloodRequestAPI, createWebSocket } from '../services/api';
import useAuthStore from '../store/authStore';

const DonationHistory = () => {
  const { user, token } = useAuthStore();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadHistory();
    
    // Setup WebSocket for real-time updates
    let websocket;
    if (token) {
      try {
        websocket = createWebSocket(token);
        
        websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          // Reload history when donation is confirmed or new response received
          if (message.type === 'notification' && 
              (message.notification_type === 'donation_confirmed' || 
               message.notification_type === 'donor_accepted' ||
               message.notification_type === 'request_fulfilled')) {
            console.log('📜 Reloading Donation History due to:', message.notification_type);
            loadHistory();
          }
        };
        
        websocket.onerror = (error) => {
          console.error('WebSocket error in DonationHistory:', error);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
      }
    }
    
    // Auto-refresh every 30 seconds as fallback
    const refreshInterval = setInterval(() => {
      loadHistory();
    }, 30000);
    
    return () => {
      if (websocket) {
        websocket.close();
      }
      clearInterval(refreshInterval);
    };
  }, [token]);

  const loadHistory = async () => {
    try {
      const response = await bloodRequestAPI.getDonationHistory(50);
      setHistory(response.data);
    } catch (error) {
      console.error('Error loading donation history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyBadge = (urgency) => {
    const styles = {
      critical: { bg: '#fee2e2', color: '#991b1b', label: '🚨 CRITICAL' },
      urgent: { bg: '#fef3c7', color: '#92400e', label: '⚠️ URGENT' },
      normal: { bg: '#dbeafe', color: '#1e40af', label: '📋 NORMAL' }
    };
    const style = styles[urgency] || styles.normal;
    
    return (
      <span style={{
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: 'bold',
        backgroundColor: style.bg,
        color: style.color
      }}>
        {style.label}
      </span>
    );
  };

  const getStatusBadge = (status) => {
    const styles = {
      accepted: { bg: '#fef3c7', color: '#92400e', label: '✅ Accepted' },
      donated: { bg: '#d1fae5', color: '#065f46', label: '🩸 Donated' },
      fulfilled: { bg: '#d1fae5', color: '#065f46', label: '✅ Fulfilled' },
      rejected: { bg: '#fee2e2', color: '#991b1b', label: '❌ Rejected' },
      pending: { bg: '#f3f4f6', color: '#6b7280', label: '⏳ Pending' }
    };
    const style = styles[status.toLowerCase()] || styles.pending;
    
    return (
      <span style={{
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '11px',
        fontWeight: 'bold',
        backgroundColor: style.bg,
        color: style.color
      }}>
        {style.label}
      </span>
    );
  };

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', color: '#6b7280' }}>Loading donation history...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center' }}>
        <h3 style={{ marginBottom: '10px' }}>📜 Donation History</h3>
        <p style={{ color: '#6b7280' }}>
          No donation activity yet. Accept blood requests or create requests to see your history here.
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        📜 Donation History ({history.length})
      </h3>
      
      <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
        {history.map((item, index) => (
          <div 
            key={item.id}
            style={{
              padding: '15px',
              marginBottom: '12px',
              backgroundColor: index % 2 === 0 ? '#f9fafb' : '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              borderLeft: '4px solid #ef4444'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
              <div>
                <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '5px' }}>
                  {new Date(item.date).toLocaleDateString()} at {new Date(item.date).toLocaleTimeString()}
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1f2937', marginBottom: '5px' }}>
                  {item.requester_name ? (
                    <>
                      {item.status === 'donated' ? '🩸 Donated to:' : '✅ Accepted to:'} {item.requester_name}
                    </>
                  ) : (
                    <>
                      ✅ Accepted from: {item.donor_name}
                      {item.donor_name !== 'Other Source' && item.donor_blood_group !== '-' && (
                        <> ({item.donor_blood_group})</>
                      )}
                      {(item.donor_name === 'Other Source' || item.fulfillment_source === 'other') && (
                        <> (Other Source)</>
                      )}
                    </>
                  )}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                {getUrgencyBadge(item.urgency)}
                <div style={{ marginTop: '5px' }}>
                  {getStatusBadge(item.status)}
                </div>
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px', marginTop: '10px' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '2px' }}>Blood Group</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#ef4444' }}>{item.blood_group}</div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '2px' }}>Units</div>
                <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#1f2937' }}>{item.units} unit(s)</div>
              </div>
              {item.address && item.requester_name && (
                <div style={{ gridColumn: '1 / -1' }}>
                  <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '2px' }}>Location</div>
                  <div style={{ fontSize: '14px', color: '#4b5563' }}>{item.address}</div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {history.length >= 50 && (
        <div style={{
          marginTop: '10px',
          padding: '10px',
          backgroundColor: '#f3f4f6',
          borderRadius: '6px',
          textAlign: 'center',
          fontSize: '13px',
          color: '#6b7280'
        }}>
          Showing last 50 entries
        </div>
      )}
    </div>
  );
};

export default DonationHistory;
