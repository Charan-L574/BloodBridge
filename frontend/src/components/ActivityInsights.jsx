import React, { useState, useEffect } from 'react';
import { bloodRequestAPI, createWebSocket } from '../services/api';
import useAuthStore from '../store/authStore';

const ActivityInsights = () => {
  const { user, token } = useAuthStore();
  const [donorInsights, setDonorInsights] = useState(null);
  const [requesterInsights, setRequesterInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('donor');

  useEffect(() => {
    loadInsights();
    
    // Setup WebSocket for real-time updates
    let websocket;
    if (token) {
      try {
        websocket = createWebSocket(token);
        
        websocket.onmessage = (event) => {
          const message = JSON.parse(event.data);
          
          // Reload insights when donation is confirmed or request is fulfilled
          if (message.type === 'notification' && 
              (message.notification_type === 'donation_confirmed' || 
               message.notification_type === 'request_fulfilled')) {
            console.log('📊 Reloading Activity Insights due to:', message.notification_type);
            loadInsights();
          }
        };
        
        websocket.onerror = (error) => {
          console.error('WebSocket error in ActivityInsights:', error);
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
      }
    }
    
    // Auto-refresh every 30 seconds as fallback
    const refreshInterval = setInterval(() => {
      loadInsights();
    }, 30000);
    
    return () => {
      if (websocket) {
        websocket.close();
      }
      clearInterval(refreshInterval);
    };
  }, [token]);

  const loadInsights = async () => {
    try {
      const [historyRes, requestsRes] = await Promise.all([
        bloodRequestAPI.getDonationHistory(100).catch(() => ({ data: [] })),
        bloodRequestAPI.getRequests().catch(() => ({ data: [] }))
      ]);
      
      const history = historyRes.data || [];
      const requests = requestsRes.data || [];
      
      console.log('🔍 Activity Insights - Raw History Data:', history);
      
      // Calculate donor insights (from history - donations made by current user)
      // Only count donations where user was the donor (has requester_name field)
      // DONATED status = requester confirmed the donation
      // ACCEPTED status = donor accepted but not yet confirmed by requester
      const donorHistory = history.filter(h => h.requester_name); // Donations made
      console.log('🩸 Donor History (has requester_name):', donorHistory);
      
      const confirmedDonations = donorHistory.filter(h => h.status === 'donated');
      console.log('✅ Confirmed Donations (status === "donated"):', confirmedDonations);
      
      const acceptedDonations = donorHistory.filter(h => h.status === 'accepted');
      console.log('⏳ Accepted Donations (status === "accepted" - awaiting confirmation):', acceptedDonations);
      
      const dInsights = {
        totalDonations: confirmedDonations.length, // Only count confirmed donations
        acceptedPending: acceptedDonations.length, // Track accepted but not confirmed
        last30Days: confirmedDonations.filter(h => {
          const date = new Date(h.date);
          const thirtyDaysAgo = new Date();
          thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
          return date >= thirtyDaysAgo;
        }).length,
        bloodGroups: {},
        lifetimeImpact: confirmedDonations.length * 3
      };
      
      confirmedDonations.forEach(h => {
        const bloodGroup = h.blood_group || 'Unknown';
        dInsights.bloodGroups[bloodGroup] = (dInsights.bloodGroups[bloodGroup] || 0) + 1;
      });
      
      const mostDonated = Object.entries(dInsights.bloodGroups).sort((a, b) => b[1] - a[1])[0];
      dInsights.mostDonatedGroup = mostDonated ? mostDonated[0] : 'N/A';
      
      setDonorInsights(dInsights);
      
      // Calculate requester insights (from requests made)
      const rInsights = {
        totalRequests: requests.length,
        fulfilledRequests: requests.filter(r => r.status === 'fulfilled').length,
        pendingRequests: requests.filter(r => r.status === 'pending').length,
        urgencyBreakdown: {
          critical: requests.filter(r => r.urgency_level === 'critical').length,
          urgent: requests.filter(r => r.urgency_level === 'urgent').length,
          normal: requests.filter(r => r.urgency_level === 'normal').length
        }
      };
      rInsights.fulfillmentRate = rInsights.totalRequests > 0 
        ? ((rInsights.fulfilledRequests / rInsights.totalRequests) * 100).toFixed(1) 
        : 0;
      
      setRequesterInsights(rInsights);
      
      // Set default tab based on user role
      if (user?.role === 'requester' || user?.role === 'hospital') {
        setActiveTab('requester');
      }
    } catch (error) {
      console.error('Error loading insights:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="card" style={{ textAlign: 'center', color: '#6b7280' }}>Loading activity insights...</div>;
  }

  return (
    <div className="card">
      <h3 style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        📊 Activity Insights
      </h3>
      
      {/* Tab Buttons - UNIVERSAL for all users */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        <button
          onClick={() => setActiveTab('donor')}
          style={{
            flex: 1,
            padding: '12px',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            backgroundColor: activeTab === 'donor' ? '#ef4444' : '#f3f4f6',
            color: activeTab === 'donor' ? 'white' : '#6b7280',
            transition: 'all 0.2s'
          }}
        >
          🩸 Donor Activity
        </button>
        <button
          onClick={() => setActiveTab('requester')}
          style={{
            flex: 1,
            padding: '12px',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: 'bold',
            backgroundColor: activeTab === 'requester' ? '#3b82f6' : '#f3f4f6',
            color: activeTab === 'requester' ? 'white' : '#6b7280',
            transition: 'all 0.2s'
          }}
        >
          📋 Requester Activity
        </button>
      </div>
      
      {/* Donor Activity View */}
      {activeTab === 'donor' && donorInsights && (
        <div>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', 
            gap: '12px',
            marginBottom: '15px'
          }}>
            <div style={{
              padding: '15px',
              backgroundColor: '#fef2f2',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#dc2626' }}>
                {donorInsights.totalDonations}
              </div>
              <div style={{ fontSize: '12px', color: '#991b1b' }}>Total Donations</div>
            </div>
            
            <div style={{
              padding: '15px',
              backgroundColor: '#fef3c7',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#d97706' }}>
                {donorInsights.last30Days}
              </div>
              <div style={{ fontSize: '12px', color: '#92400e' }}>Last 30 Days</div>
            </div>
            
            <div style={{
              padding: '15px',
              backgroundColor: '#fee2e2',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc2626' }}>
                {donorInsights.mostDonatedGroup}
              </div>
              <div style={{ fontSize: '12px', color: '#991b1b' }}>Most Donated</div>
            </div>
          </div>
          
          <div style={{
            padding: '20px',
            backgroundColor: '#f0fdf4',
            borderRadius: '8px',
            textAlign: 'center',
            border: '2px solid #86efac'
          }}>
            <div style={{ fontSize: '14px', color: '#15803d', marginBottom: '5px' }}>
              🌟 Estimated Lives Saved
            </div>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#166534' }}>
              ~{donorInsights.lifetimeImpact}
            </div>
            <div style={{ fontSize: '11px', color: '#16a34a', marginTop: '5px' }}>
              Each donation can save up to 3 lives!
            </div>
          </div>
          
          {donorInsights.acceptedCount > 0 && (
            <div style={{
              marginTop: '15px',
              padding: '15px',
              backgroundColor: '#eff6ff',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#1e40af',
              textAlign: 'center'
            }}>
              ℹ️ You have <strong>{donorInsights.acceptedCount}</strong> accepted request(s) pending confirmation from requester.
            </div>
          )}
          
          {donorInsights.totalDonations === 0 && (
            <div style={{
              marginTop: '15px',
              padding: '15px',
              backgroundColor: '#eff6ff',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#1e40af',
              textAlign: 'center'
            }}>
              💡 Start donating blood to see your impact here!
            </div>
          )}
        </div>
      )}
      
      {/* Requester Activity View */}
      {activeTab === 'requester' && requesterInsights && (
        <div>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', 
            gap: '12px',
            marginBottom: '15px'
          }}>
            <div style={{
              padding: '15px',
              backgroundColor: '#eff6ff',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1e40af' }}>
                {requesterInsights.totalRequests}
              </div>
              <div style={{ fontSize: '12px', color: '#1e40af' }}>Total Requests</div>
            </div>
            
            <div style={{
              padding: '15px',
              backgroundColor: '#d1fae5',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#047857' }}>
                {requesterInsights.fulfilledRequests}
              </div>
              <div style={{ fontSize: '12px', color: '#065f46' }}>Fulfilled</div>
            </div>
            
            <div style={{
              padding: '15px',
              backgroundColor: '#fef3c7',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#d97706' }}>
                {requesterInsights.pendingRequests}
              </div>
              <div style={{ fontSize: '12px', color: '#92400e' }}>Pending</div>
            </div>
          </div>
          
          {/* Fulfillment Rate */}
          <div style={{
            padding: '15px',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
            marginBottom: '15px'
          }}>
            <div style={{ fontSize: '14px', color: '#4b5563', marginBottom: '8px' }}>
              📈 Fulfillment Rate
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ flex: 1, height: '10px', backgroundColor: '#e5e7eb', borderRadius: '5px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${requesterInsights.fulfillmentRate}%`,
                  backgroundColor: requesterInsights.fulfillmentRate >= 70 ? '#10b981' : 
                                  requesterInsights.fulfillmentRate >= 40 ? '#f59e0b' : '#ef4444',
                  transition: 'width 0.3s ease'
                }}></div>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937', minWidth: '60px' }}>
                {requesterInsights.fulfillmentRate}%
              </div>
            </div>
          </div>
          
          {/* Urgency Breakdown */}
          <div style={{
            padding: '15px',
            backgroundColor: '#f9fafb',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '14px', color: '#4b5563', marginBottom: '10px' }}>
              🚨 Requests by Urgency
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ef4444' }}>
                  {requesterInsights.urgencyBreakdown.critical}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>Critical</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#f59e0b' }}>
                  {requesterInsights.urgencyBreakdown.urgent}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>Urgent</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                  {requesterInsights.urgencyBreakdown.normal}
                </div>
                <div style={{ fontSize: '11px', color: '#6b7280' }}>Normal</div>
              </div>
            </div>
          </div>
          
          {requesterInsights.totalRequests === 0 && (
            <div style={{
              marginTop: '15px',
              padding: '15px',
              backgroundColor: '#eff6ff',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#1e40af',
              textAlign: 'center'
            }}>
              💡 Create blood requests to see your activity here!
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ActivityInsights;
