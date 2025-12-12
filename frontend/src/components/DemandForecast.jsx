import React, { useState, useEffect } from 'react';
import { bloodRequestAPI } from '../services/api';

const DemandForecast = () => {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [daysFilter, setDaysFilter] = useState(7);

  useEffect(() => {
    loadForecast();
  }, [daysFilter]);

  const loadForecast = async () => {
    try {
      const response = await bloodRequestAPI.getDemandForecast(daysFilter);
      setForecast(response.data);
    } catch (error) {
      console.error('Error loading forecast:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend) => {
    switch(trend) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      case 'stable': return '➡️';
      default: return '❓';
    }
  };

  const getSupplyStatusColor = (status) => {
    switch(status) {
      case 'sufficient': return '#10b981';
      case 'low': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getUrgencyColor = (score) => {
    if (score >= 75) return '#ef4444';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#eab308';
    return '#10b981';
  };

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', color: '#6b7280' }}>Loading demand forecast...</div>;
  }

  if (!forecast) {
    return <div className="card" style={{ textAlign: 'center', color: '#6b7280' }}>Unable to load forecast data.</div>;
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          📊 Blood Demand Forecast
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
          <option value={7}>Next 7 days</option>
          <option value={14}>Next 14 days</option>
          <option value={30}>Next 30 days</option>
        </select>
      </div>

      {/* Summary Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '15px',
        marginBottom: '20px'
      }}>
        <div style={{
          padding: '15px',
          backgroundColor: '#eff6ff',
          borderRadius: '8px',
          border: '2px solid #3b82f6'
        }}>
          <div style={{ fontSize: '13px', color: '#1e40af', marginBottom: '5px' }}>Total Predicted Demand</div>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1e3a8a' }}>
            {forecast.total_predicted_units} units
          </div>
        </div>

        {forecast.high_demand_groups.length > 0 && (
          <div style={{
            padding: '15px',
            backgroundColor: '#fef2f2',
            borderRadius: '8px',
            border: '2px solid #ef4444'
          }}>
            <div style={{ fontSize: '13px', color: '#991b1b', marginBottom: '5px' }}>High Priority Groups</div>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#7f1d1d' }}>
              {forecast.high_demand_groups.join(', ')}
            </div>
          </div>
        )}
      </div>

      {/* Blood Group Forecasts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '15px' }}>
        {Object.entries(forecast.by_blood_group).map(([bloodGroup, data]) => (
          <div 
            key={bloodGroup}
            style={{
              padding: '15px',
              backgroundColor: '#ffffff',
              border: '2px solid #e5e7eb',
              borderRadius: '8px',
              borderLeft: `6px solid ${getUrgencyColor(data.urgency_score)}`
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
                {bloodGroup}
              </div>
              <div style={{ fontSize: '24px' }}>
                {getTrendIcon(data.trend)}
              </div>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', color: '#6b7280' }}>Predicted Demand</div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937' }}>
                {data.predicted_units} units
              </div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                ~{data.predicted_requests} requests
              </div>
            </div>

            <div style={{ marginBottom: '10px' }}>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '3px' }}>Available Donors</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1f2937' }}>
                  {data.available_donors}
                </div>
                <div style={{
                  padding: '3px 8px',
                  borderRadius: '12px',
                  fontSize: '10px',
                  fontWeight: 'bold',
                  backgroundColor: getSupplyStatusColor(data.supply_status),
                  color: 'white'
                }}>
                  {data.supply_status.toUpperCase()}
                </div>
              </div>
            </div>

            <div style={{
              padding: '8px',
              backgroundColor: '#f9fafb',
              borderRadius: '6px',
              marginTop: '10px'
            }}>
              <div style={{ 
                fontSize: '11px', 
                color: '#4b5563',
                lineHeight: '1.4'
              }}>
                {data.recommendation}
              </div>
            </div>

            {/* Urgency Meter */}
            <div style={{ marginTop: '10px' }}>
              <div style={{ fontSize: '10px', color: '#9ca3af', marginBottom: '3px' }}>
                Urgency Level: {data.urgency_score}%
              </div>
              <div style={{
                height: '6px',
                backgroundColor: '#e5e7eb',
                borderRadius: '3px',
                overflow: 'hidden'
              }}>
                <div style={{
                  height: '100%',
                  width: `${data.urgency_score}%`,
                  backgroundColor: getUrgencyColor(data.urgency_score),
                  transition: 'width 0.3s ease'
                }}></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{
        marginTop: '20px',
        padding: '15px',
        backgroundColor: '#f0f9ff',
        borderRadius: '8px',
        border: '1px solid #bae6fd'
      }}>
        <div style={{ fontSize: '13px', color: '#075985', lineHeight: '1.6' }}>
          <strong>📌 About this forecast:</strong> Predictions are based on historical request patterns from the last 30 days. 
          High urgency scores indicate increasing demand. Regularly check forecasts and coordinate with donors to maintain adequate supply.
        </div>
      </div>

      <div style={{ 
        marginTop: '10px', 
        fontSize: '11px', 
        color: '#9ca3af', 
        textAlign: 'right' 
      }}>
        Generated: {new Date(forecast.generated_at).toLocaleString()}
      </div>
    </div>
  );
};

export default DemandForecast;
