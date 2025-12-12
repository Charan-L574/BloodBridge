import React, { useState } from 'react';

const HealthCheckModal = ({ isOpen, onClose, onSubmit, requestId }) => {
  const [formData, setFormData] = useState({
    has_consumed_alcohol_24h: false,
    has_smoked_24h: false,
    has_taken_medication: false,
    has_recent_illness: false,
    has_recent_surgery: false,
    has_tattoo_piercing_6months: false,
    enable_live_tracking: false,
    use_saved_location: true,
  });

  const [additionalInfo, setAdditionalInfo] = useState('');

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : e.target.value
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ ...formData, additional_info: additionalInfo, blood_request_id: requestId });
  };

  const hasAnyRestrictions = 
    formData.has_consumed_alcohol_24h ||
    formData.has_smoked_24h ||
    formData.has_taken_medication ||
    formData.has_recent_illness ||
    formData.has_recent_surgery ||
    formData.has_tattoo_piercing_6months;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.7)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '8px',
        padding: '30px',
        maxWidth: '600px',
        width: '100%',
        maxHeight: '90vh',
        overflow: 'auto',
        color: '#333'
      }}>
        <h2 style={{ marginTop: 0, color: '#dc2626' }}>🩺 Health Eligibility Check</h2>
        <p style={{ color: '#6b7280', marginBottom: '20px' }}>
          Please answer these questions honestly. Your health and safety are our top priority.
        </p>

        <form onSubmit={handleSubmit}>
          {/* Health Questions */}
          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#374151' }}>
              Health Status (Last 24 Hours)
            </h3>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="has_consumed_alcohol_24h"
                checked={formData.has_consumed_alcohol_24h}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>I have consumed alcohol in the last 24 hours</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="has_smoked_24h"
                checked={formData.has_smoked_24h}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>I have smoked/used tobacco in the last 24 hours</span>
            </label>
          </div>

          <div style={{ marginBottom: '25px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#374151' }}>
              Recent Medical History
            </h3>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="has_taken_medication"
                checked={formData.has_taken_medication}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>I am currently taking medication (especially antibiotics or aspirin)</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="has_recent_illness"
                checked={formData.has_recent_illness}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>I have had fever, cold, or flu in the last 2 weeks</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="has_recent_surgery"
                checked={formData.has_recent_surgery}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>I have had surgery in the last 6 months</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="has_tattoo_piercing_6months"
                checked={formData.has_tattoo_piercing_6months}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>I have gotten a tattoo or piercing in the last 6 months</span>
            </label>
          </div>

          {/* Additional Info */}
          <div style={{ marginBottom: '25px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Additional Information (Optional)
            </label>
            <textarea
              value={additionalInfo}
              onChange={(e) => setAdditionalInfo(e.target.value)}
              placeholder="Any other health conditions or concerns..."
              rows="3"
              style={{
                width: '100%',
                padding: '10px',
                borderRadius: '4px',
                border: '1px solid #d1d5db',
                fontSize: '14px'
              }}
            />
          </div>

          {/* Location Preference */}
          <div style={{ marginBottom: '25px', borderTop: '1px solid #e5e7eb', paddingTop: '20px' }}>
            <h3 style={{ fontSize: '16px', marginBottom: '15px', color: '#374151' }}>
              📍 Location Sharing Preference
            </h3>

            <label style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '12px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="enable_live_tracking"
                checked={formData.enable_live_tracking}
                onChange={handleChange}
                style={{ marginRight: '10px', marginTop: '3px' }}
              />
              <span>Enable Live GPS Tracking (recommended)</span>
            </label>

            <p style={{ fontSize: '13px', color: '#6b7280', marginLeft: '30px', marginTop: '-8px' }}>
              {formData.enable_live_tracking ? 
                '✓ Requester will see your real-time location for faster coordination' :
                'ℹ️ Requester will only see your saved location'
              }
            </p>
          </div>

          {/* Warning */}
          {hasAnyRestrictions && (
            <div style={{
              background: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '6px',
              padding: '15px',
              marginBottom: '20px'
            }}>
              <p style={{ color: '#dc2626', margin: 0, fontSize: '14px' }}>
                ⚠️ <strong>Warning:</strong> Some of your responses may make you temporarily ineligible to donate. 
                The system will verify and inform you.
              </p>
            </div>
          )}

          {/* Buttons */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '25px' }}>
            <button
              type="submit"
              style={{
                flex: 1,
                padding: '12px',
                background: hasAnyRestrictions ? '#dc2626' : '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              {hasAnyRestrictions ? 'Submit (May Be Rejected)' : 'Accept Request'}
            </button>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1,
                padding: '12px',
                background: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '16px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default HealthCheckModal;
