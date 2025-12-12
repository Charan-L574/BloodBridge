import React, { useState, useEffect } from 'react';
import { hospitalAPI } from '../services/api';

const ExpiryAlerts = () => {
  const [expiringInventory, setExpiringInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [daysFilter, setDaysFilter] = useState(7);

  useEffect(() => {
    loadExpiringInventory();
    
    // Refresh every 5 minutes
    const interval = setInterval(loadExpiringInventory, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [daysFilter]);

  const loadExpiringInventory = async () => {
    try {
      const response = await hospitalAPI.getExpiringSoon(daysFilter);
      setExpiringInventory(response.data);
    } catch (error) {
      console.error('Error loading expiring inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysUntilExpiry = (expiryDate) => {
    const today = new Date();
    const expiry = new Date(expiryDate);
    const diffTime = expiry - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getUrgencyColor = (days) => {
    if (days <= 2) return '#ef4444'; // Red
    if (days <= 5) return '#f59e0b'; // Orange
    return '#eab308'; // Yellow
  };

  if (loading) {
    return <div style={{ color: '#6b7280' }}>Loading expiry alerts...</div>;
  }

  if (expiringInventory.length === 0) {
    return (
      <div className="card" style={{ backgroundColor: '#f0fdf4', border: '1px solid #86efac' }}>
        <h3 style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          ✅ Inventory Status
        </h3>
        <p style={{ color: '#15803d', margin: 0 }}>
          No blood units expiring in the next {daysFilter} days. All inventory is fresh!
        </p>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          ⚠️ Expiry Alerts ({expiringInventory.length})
        </h3>
        <select 
          value={daysFilter} 
          onChange={(e) => setDaysFilter(Number(e.target.value))}
          style={{
            padding: '5px 10px',
            borderRadius: '4px',
            border: '1px solid #d1d5db'
          }}
        >
          <option value={3}>Next 3 days</option>
          <option value={7}>Next 7 days</option>
          <option value={14}>Next 14 days</option>
          <option value={30}>Next 30 days</option>
        </select>
      </div>

      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {expiringInventory.map((item, index) => {
          const daysLeft = getDaysUntilExpiry(item.expiry_date);
          const urgencyColor = getUrgencyColor(daysLeft);
          
          return (
            <div 
              key={index}
              style={{
                padding: '12px',
                marginBottom: '10px',
                backgroundColor: '#fef2f2',
                border: `2px solid ${urgencyColor}`,
                borderRadius: '8px',
                borderLeft: `6px solid ${urgencyColor}`
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ 
                    fontSize: '18px', 
                    fontWeight: 'bold',
                    color: urgencyColor,
                    marginBottom: '5px'
                  }}>
                    {item.blood_group}
                  </div>
                  <div style={{ fontSize: '14px', color: '#6b7280' }}>
                    <strong>{item.units_available}</strong> units available
                  </div>
                  <div style={{ fontSize: '13px', color: '#9ca3af', marginTop: '3px' }}>
                    Expires: {new Date(item.expiry_date).toLocaleDateString()}
                  </div>
                </div>
                <div style={{
                  padding: '8px 12px',
                  backgroundColor: urgencyColor,
                  color: 'white',
                  borderRadius: '20px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  textAlign: 'center',
                  minWidth: '80px'
                }}>
                  {daysLeft === 0 ? 'TODAY' : 
                   daysLeft === 1 ? 'TOMORROW' :
                   `${daysLeft} DAYS`}
                </div>
              </div>
              
              {daysLeft <= 2 && (
                <div style={{
                  marginTop: '10px',
                  padding: '8px',
                  backgroundColor: '#fee2e2',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: '#991b1b'
                }}>
                  <strong>URGENT:</strong> Use these units immediately or consider transferring to another facility.
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div style={{
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#fef9c3',
        borderRadius: '6px',
        fontSize: '13px',
        color: '#854d0e'
      }}>
        💡 <strong>Tip:</strong> Schedule regular inventory reviews and coordinate with other hospitals for blood unit transfers when needed.
      </div>
    </div>
  );
};

export default ExpiryAlerts;
