import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { bloodRequestAPI, createWebSocket } from '../services/api';
import useAuthStore from '../store/authStore';
import NotificationToast from '../components/NotificationToast';
import ExpiryAlerts from '../components/ExpiryAlerts';
import NotificationSidebar from '../components/NotificationSidebar';
import UniversalDirectionsModal from '../components/UniversalDirectionsModal';

// Component to handle map clicks
const MapClickHandler = ({ onLocationSelect }) => {
  useMapEvents({
    click: (e) => {
      onLocationSelect(e.latlng);
    },
  });
  return null;
};

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

const RequesterDashboard = () => {
  const { user, token } = useAuthStore();
  const [myRequests, setMyRequests] = useState([]);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [matchingDonors, setMatchingDonors] = useState([]);
  const [donorResponses, setDonorResponses] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [ws, setWs] = useState(null);
  const [liveLocations, setLiveLocations] = useState({});
  const [notifications, setNotifications] = useState([]);
  const [routes, setRoutes] = useState({});
  const [selectedDonor, setSelectedDonor] = useState(null);
  const [showDirectionsModal, setShowDirectionsModal] = useState(false);
  const [directionsData, setDirectionsData] = useState(null);
  
  const [newRequest, setNewRequest] = useState({
    blood_group: 'O+',
    units_needed: 1,
    latitude: 40.7128,
    longitude: -74.0060,
    address: '',
    urgency_level: 'normal',
    description: ''
  });
  
  useEffect(() => {
    loadMyRequests();
    
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
        
        if (message.type === 'location_update') {
          setLiveLocations(prev => ({
            ...prev,
            [message.data.donor_response_id]: {
              latitude: message.data.latitude,
              longitude: message.data.longitude,
              timestamp: message.data.timestamp
            }
          }));
        } else if (message.type === 'notification') {
          // Add notification to display
          console.log('🔔 RequesterDashboard notification:', message);
          setNotifications(prev => {
            const newNotifications = [...prev, { ...message, id: Date.now() }];
            console.log('📋 Updated notifications array:', newNotifications);
            return newNotifications;
          });
          
          // Reload requests list when relevant updates occur
          if (message.notification_type === 'request_fulfilled' || 
              message.notification_type === 'donation_confirmed' ||
              message.notification_type === 'donor_accepted') {
            console.log('🔄 Reloading requests due to:', message.notification_type);
            loadMyRequests();
          }
          
          // Reload responses if it's about current selected request
          if (selectedRequest && message.data.request_id === selectedRequest.id) {
            bloodRequestAPI.getResponses(selectedRequest.id)
              .then(res => setDonorResponses(res.data))
              .catch(err => console.error('Error reloading responses:', err));
          }
        }
      };
      
      setWs(websocket);
      
      return () => {
        console.log('🔌 Closing RequesterDashboard WebSocket...');
        websocket.close();
      };
    }
  }, [token]);
  
  const loadMyRequests = async () => {
    try {
      const response = await bloodRequestAPI.getRequests();
      setMyRequests(response.data);
    } catch (error) {
      console.error('Error loading requests:', error);
    }
  };
  
  const handleCreateRequest = async (e) => {
    e.preventDefault();
    try {
      await bloodRequestAPI.createRequest(newRequest);
      alert('Blood request created successfully!');
      setShowCreateForm(false);
      loadMyRequests();
      setNewRequest({
        blood_group: 'O+',
        units_needed: 1,
        latitude: 40.7128,
        longitude: -74.0060,
        address: '',
        urgency_level: 'normal',
        description: ''
      });
    } catch (error) {
      alert('Error creating request: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };
  
  const handleSelectRequest = async (request) => {
    setSelectedRequest(request);
    
    // Find matching donors
    try {
      const [donorsRes, responsesRes] = await Promise.all([
        bloodRequestAPI.findMatchingDonors(request.id, 6),
        bloodRequestAPI.getResponses(request.id)
      ]);
      setMatchingDonors(donorsRes.data);
      setDonorResponses(responsesRes.data);
      
      // Watch this request via WebSocket
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'watch_request',
          data: { request_id: request.id }
        }));
      }
    } catch (error) {
      console.error('Error loading donors:', error);
    }
  };
  
  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        setNewRequest(prev => ({
          ...prev,
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        }));
      });
    }
  };

  const fetchRoute = async (startLat, startLng, endLat, endLng) => {
    try {
      const apiKey = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImI1ZDM4MTM3NjM2YjQxOTQ4NmQxMWM4NTI3MzAzNjI0IiwiaCI6Im11cm11cjY0In0=';
      const url = `https://api.openrouteservice.org/v2/directions/driving-car?api_key=${apiKey}&start=${startLng},${startLat}&end=${endLng},${endLat}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.features && data.features[0]) {
        const coords = data.features[0].geometry.coordinates;
        // Convert from [lng, lat] to [lat, lng]
        return coords.map(c => [c[1], c[0]]);
      }
      return null;
    } catch (error) {
      console.error('Error fetching route:', error);
      return null;
    }
  };

  const handleShowRoute = async (donor) => {
    setSelectedDonor(donor);
    const routeKey = `${donor.donor_id}`;
    
    if (!routes[routeKey]) {
      const routeCoords = await fetchRoute(
        donor.location.latitude,
        donor.location.longitude,
        selectedRequest.latitude,
        selectedRequest.longitude
      );
      
      if (routeCoords) {
        setRoutes(prev => ({ ...prev, [routeKey]: routeCoords }));
      }
    }
  };

  const [showFulfillmentModal, setShowFulfillmentModal] = useState(false);
  const [acceptedDonors, setAcceptedDonors] = useState([]);
  const [fulfillmentRequestId, setFulfillmentRequestId] = useState(null);

  const handleMarkAsFulfilled = async (requestId) => {
    setFulfillmentRequestId(requestId);
    
    try {
      // Fetch accepted donors for this request
      const response = await bloodRequestAPI.getAcceptedDonors(requestId);
      setAcceptedDonors(response.data);
      setShowFulfillmentModal(true);
    } catch (error) {
      console.error('Error fetching accepted donors:', error);
      alert('Error loading accepted donors: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const handleConfirmFulfillment = async (donorId, source) => {
    try {
      await bloodRequestAPI.updateStatus(fulfillmentRequestId, 'fulfilled', donorId, source);
      alert('✅ Request marked as fulfilled!');
      setShowFulfillmentModal(false);
      loadMyRequests();
    } catch (error) {
      alert('Error: ' + (error.response?.data?.detail || 'Failed to update'));
    }
  };
  
  return (
    <div style={{ display: 'flex', gap: '20px', width: '100%', padding: '20px', margin: '0', alignItems: 'flex-start' }}>
      <div style={{ flex: 1 }}>
      
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Blood Request Dashboard</h2>
            <p style={{ color: '#6b7280', marginTop: '10px' }}>
              Manage your blood requests and track donors
            </p>
          </div>
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? 'Cancel' : '+ New Request'}
          </button>
        </div>
      </div>
      
      {/* Expiry Alerts for Hospital Users */}
      {user?.role === 'hospital' && (
        <ExpiryAlerts />
      )}
      
      {showCreateForm && (
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>Create Blood Request</h3>
          <form onSubmit={handleCreateRequest}>
            <div className="grid grid-2">
              <div className="form-group">
                <label>Blood Group *</label>
                <select 
                  value={newRequest.blood_group}
                  onChange={(e) => setNewRequest({...newRequest, blood_group: e.target.value})}
                  required
                >
                  {BLOOD_GROUPS.map(group => (
                    <option key={group} value={group}>{group}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>Units Needed *</label>
                <input
                  type="number"
                  min="1"
                  value={newRequest.units_needed}
                  onChange={(e) => setNewRequest({...newRequest, units_needed: parseInt(e.target.value)})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Urgency Level *</label>
                <select
                  value={newRequest.urgency_level}
                  onChange={(e) => setNewRequest({...newRequest, urgency_level: e.target.value})}
                >
                  <option value="normal">Normal</option>
                  <option value="urgent">Urgent</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
              
              <div className="form-group">
                <label>Location</label>
                <button 
                  type="button"
                  className="btn btn-secondary" 
                  onClick={getCurrentLocation}
                  style={{ width: '100%' }}
                >
                  📍 Use My Location
                </button>
              </div>
            </div>
            
            <div className="form-group">
              <label>Address</label>
              <input
                type="text"
                value={newRequest.address}
                onChange={(e) => setNewRequest({...newRequest, address: e.target.value})}
                placeholder="Enter location address"
              />
            </div>
            
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newRequest.description}
                onChange={(e) => setNewRequest({...newRequest, description: e.target.value})}
                rows="3"
                placeholder="Additional information..."
              />
            </div>
            
            <div className="form-group">
              <label>Click on map to set location</label>
              <div style={{ height: '300px', marginTop: '10px', borderRadius: '8px', overflow: 'hidden', border: '2px solid #e5e7eb' }}>
                <MapContainer 
                  center={[newRequest.latitude, newRequest.longitude]} 
                  zoom={13} 
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  />
                  <MapClickHandler 
                    onLocationSelect={(latlng) => {
                      setNewRequest(prev => ({
                        ...prev,
                        latitude: latlng.lat,
                        longitude: latlng.lng
                      }));
                    }}
                  />
                  <Marker position={[newRequest.latitude, newRequest.longitude]}>
                    <Popup>Request Location</Popup>
                  </Marker>
                </MapContainer>
              </div>
              <small style={{ color: '#6b7280' }}>
                📍 Lat: {newRequest.latitude.toFixed(6)}, Lng: {newRequest.longitude.toFixed(6)}
              </small>
            </div>
            
            <button type="submit" className="btn btn-primary">
              Create Request
            </button>
          </form>
        </div>
      )}
      
      <div className="grid grid-2">
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>My Requests</h3>
          {myRequests.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No requests yet. Create your first request above.</p>
          ) : (
            <div>
              {myRequests.map(req => (
                <div 
                  key={req.id} 
                  style={{ 
                    padding: '15px', 
                    backgroundColor: selectedRequest?.id === req.id ? '#fee2e2' : '#f9fafb',
                    borderRadius: '4px',
                    marginBottom: '10px',
                    cursor: 'pointer',
                    border: selectedRequest?.id === req.id ? '2px solid #dc2626' : 'none'
                  }}
                  onClick={() => handleSelectRequest(req)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong style={{ fontSize: '16px' }}>{req.blood_group}</strong>
                    <span className={`badge badge-${req.status === 'pending' ? 'warning' : 'success'}`}>
                      {req.status}
                    </span>
                  </div>
                  <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>
                    {req.units_needed} unit(s) - {req.urgency_level}
                  </p>
                  <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                    {new Date(req.created_at).toLocaleString()}
                  </p>
                  {req.status === 'pending' && (
                    <button
                      className="btn btn-success"
                      style={{ marginTop: '10px', width: '100%', fontSize: '13px' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleMarkAsFulfilled(req.id);
                      }}
                    >
                      ✓ Mark as Fulfilled
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>
            {selectedRequest ? `Responses for ${selectedRequest.blood_group}` : 'Select a Request'}
          </h3>
          {!selectedRequest ? (
            <p style={{ color: '#6b7280' }}>Click on a request to view matching donors and responses</p>
          ) : (
            <div>
              {/* Matching Donors Section - Always visible when request selected */}
              <div style={{ 
                marginBottom: '25px', 
                padding: '15px', 
                backgroundColor: '#f0f9ff', 
                borderRadius: '8px',
                border: '1px solid #bae6fd'
              }}>
                <h4 style={{ 
                  fontSize: '16px', 
                  marginTop: 0,
                  marginBottom: '10px',
                  color: '#0369a1',
                  fontWeight: 'bold'
                }}>
                  🩸 Nearby Available Donors
                </h4>
                <p style={{ marginBottom: '15px', color: '#0c4a6e', fontSize: '14px' }}>
                  Found <strong>{matchingDonors.length}</strong> matching donors
                  {matchingDonors.length > 0 && matchingDonors[0].distance_km > 6 && (
                    <span style={{ color: '#ea580c', marginLeft: '8px' }}>
                      (expanded to city-wide search)
                    </span>
                  )}
                </p>
                
                {matchingDonors.length === 0 ? (
                  <div style={{ 
                    padding: '20px', 
                    textAlign: 'center',
                    backgroundColor: '#fef3c7',
                    borderRadius: '6px',
                    color: '#92400e'
                  }}>
                    <p style={{ margin: 0, fontSize: '14px' }}>
                      ⚠️ No donors found in your area (searched up to 50km). Please check back later or contact hospitals directly.
                    </p>
                  </div>
                ) : (
                  <div>
                    {/* Donor cards list */}
                    {matchingDonors.slice(0, 5).map(donor => (
                      <div key={donor.donor_id} style={{
                        padding: '12px',
                        backgroundColor: 'white',
                        borderRadius: '6px',
                        marginBottom: '10px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        border: '1px solid #e0f2fe',
                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                      }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 'bold', color: '#1e293b', marginBottom: '4px' }}>
                            {donor.donor_name}
                          </div>
                          <div style={{ fontSize: '13px', color: '#64748b' }}>
                            <span style={{ 
                              display: 'inline-block',
                              padding: '2px 8px',
                              backgroundColor: '#fee2e2',
                              color: '#991b1b',
                              borderRadius: '4px',
                              marginRight: '8px',
                              fontWeight: '600'
                            }}>
                              {donor.blood_group}
                            </span>
                            <span>📍 {donor.distance_km.toFixed(2)} km away</span>
                            <span style={{ marginLeft: '10px' }}>⭐ Score: {donor.ml_score.toFixed(1)}</span>
                          </div>
                        </div>
                        <button
                          className="btn btn-primary"
                          style={{ fontSize: '13px', padding: '8px 16px' }}
                          onClick={() => handleShowRoute(donor)}
                        >
                          🗺️ View Route
                        </button>
                      </div>
                    ))}
                    {matchingDonors.length > 5 && (
                      <p style={{ textAlign: 'center', color: '#64748b', fontSize: '13px', marginTop: '10px' }}>
                        Showing top 5 of {matchingDonors.length} donors
                      </p>
                    )}
                  </div>
                )}
              </div>
              
              {/* Map with ALL donor locations (both nearby and responded) - Always show */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ marginBottom: '10px' }}>📍 Donor Locations on Map</h4>
                <div className="map-container" style={{ height: '400px' }}>
                  <MapContainer
                    center={[selectedRequest.latitude, selectedRequest.longitude]}
                    zoom={13}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    
                    {/* Request location (red marker) */}
                    <Marker 
                      position={[selectedRequest.latitude, selectedRequest.longitude]}
                      icon={L.icon({
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                      })}
                    >
                      <Popup>
                        <strong>📍 Request Location</strong>
                        <br />
                        Blood Group: {selectedRequest.blood_group}
                        <br />
                        {selectedRequest.address || 'Emergency location'}
                      </Popup>
                    </Marker>
                    
                    {/* 6km search radius circle */}
                    <Circle
                      center={[selectedRequest.latitude, selectedRequest.longitude]}
                      radius={6000}
                      pathOptions={{ color: '#dc2626', fillColor: '#fee2e2', fillOpacity: 0.15 }}
                    />
                    
                    {/* All nearby available donors (blue markers) */}
                    {matchingDonors.map((donor) => donor.location && (
                      <Marker
                        key={`available-${donor.donor_id}`}
                        position={[donor.location.latitude, donor.location.longitude]}
                        icon={L.icon({
                          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                          shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                          iconSize: [25, 41],
                          iconAnchor: [12, 41],
                        })}
                      >
                        <Popup>
                          <strong>🩸 {donor.donor_name}</strong>
                          <br />
                          Blood Group: {donor.blood_group}
                          <br />
                          Distance: {donor.distance_km.toFixed(2)} km
                          <br />
                          ML Score: {donor.ml_score.toFixed(1)}
                          <br />
                          Phone: {donor.donor_phone}
                        </Popup>
                      </Marker>
                    ))}
                    
                    {/* Donor responses (green/yellow markers) */}
                    {donorResponses.filter(r => r.location).map((response) => (
                      <Marker
                        key={`response-${response.id}`}
                        position={[response.location.latitude, response.location.longitude]}
                        icon={L.icon({
                          iconUrl: response.status === 'accepted' 
                            ? 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png'
                            : 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-yellow.png',
                          shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                          iconSize: [25, 41],
                          iconAnchor: [12, 41],
                        })}
                      >
                        <Popup>
                          <strong>{response.donor_name}</strong>
                          <br />
                          Status: {response.status}
                          <br />
                          Blood Group: {response.blood_group}
                          <br />
                          Distance: {response.distance_km?.toFixed(2)} km
                        </Popup>
                      </Marker>
                    ))}
                    
                    {/* Live tracking markers */}
                    {Object.entries(liveLocations).map(([responseId, loc]) => (
                      <Marker
                        key={`live-${responseId}`}
                        position={[loc.latitude, loc.longitude]}
                        icon={L.icon({
                          iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
                          shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                          iconSize: [25, 41],
                          iconAnchor: [12, 41],
                        })}
                      >
                        <Popup>
                          <strong>📍 Live Donor Location</strong>
                          <br />
                          Updated: {new Date(loc.timestamp).toLocaleTimeString()}
                        </Popup>
                      </Marker>
                    ))}
                  </MapContainer>
                </div>
              </div>
              
              {donorResponses.length === 0 ? (
                <p style={{ color: '#6b7280' }}>No responses yet. Donors will be notified.</p>
              ) : (
                <>
                  {/* Donor responses list */}
                  <h4 style={{ marginBottom: '10px' }}>📋 Donor Responses</h4>
                  {donorResponses.map(response => (
                    <div key={response.id} style={{ 
                      padding: '15px', 
                      backgroundColor: response.status === 'accepted' ? '#d1fae5' : '#f9fafb',
                      borderRadius: '4px',
                      marginBottom: '10px'
                    }}>
                      <strong>{response.donor_name}</strong>
                      <span className={`badge badge-${response.status === 'accepted' ? 'success' : 'warning'}`} style={{ marginLeft: '10px' }}>
                        {response.status}
                      </span>
                      <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>
                        📞 {response.donor_phone}
                      </p>
                      {response.distance_km && (
                        <p style={{ fontSize: '14px', color: '#6b7280' }}>
                          📍 {response.distance_km.toFixed(2)} km away
                        </p>
                      )}
                      {response.status === 'accepted' && response.location && (
                        <button
                          className="btn btn-primary"
                          style={{ marginTop: '10px', fontSize: '13px', width: '100%' }}
                          onClick={() => {
                            setDirectionsData({
                              start: {
                                lat: selectedRequest.latitude,
                                lng: selectedRequest.longitude,
                                label: 'Your Request Location'
                              },
                              end: {
                                lat: response.location.latitude,
                                lng: response.location.longitude,
                                label: `${response.donor_name}'s Location`
                              },
                              title: `Directions to ${response.donor_name}`,
                              description: `Navigate to donor location • Blood Group: ${response.blood_group} • Distance: ${response.distance_km.toFixed(2)} km`
                            });
                            setShowDirectionsModal(true);
                          }}
                        >
                          🗺️ Show Directions to Donor
                        </button>
                      )}
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Notification Toasts */}
      {console.log('🎨 Rendering toasts, notifications array:', notifications)}
      {notifications.map((notif, index) => {
        console.log(`🎯 Mapping notification #${index} to toast:`, notif);
        return (
          <NotificationToast
            key={notif.id}
            notification={notif}
            index={index}
            onClose={() => {
              console.log('🗑️ Closing toast:', notif.id);
              setNotifications(prev => prev.filter(n => n.id !== notif.id));
            }}
          />
        );
      })}
      
      {/* Universal Directions Modal */}
      <UniversalDirectionsModal
        isOpen={showDirectionsModal}
        onClose={() => {
          setShowDirectionsModal(false);
          setDirectionsData(null);
        }}
        startLocation={directionsData?.start}
        endLocation={directionsData?.end}
        title={directionsData?.title}
        description={directionsData?.description}
      />
      
      {/* Fulfillment Modal */}
      {showFulfillmentModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '30px',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '80vh',
            overflow: 'auto'
          }}>
            <h3 style={{ marginBottom: '20px' }}>Mark Request as Fulfilled</h3>
            <p style={{ color: '#6b7280', marginBottom: '20px' }}>
              Who provided the blood for this request?
            </p>
            
            {acceptedDonors.length > 0 ? (
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '14px', marginBottom: '10px' }}>Accepted Donors:</h4>
                {acceptedDonors.map(donor => (
                  <div 
                    key={donor.donor_id}
                    style={{
                      padding: '15px',
                      backgroundColor: '#f9fafb',
                      borderRadius: '4px',
                      marginBottom: '10px',
                      border: '1px solid #e5e7eb'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                      <div>
                        <strong>{donor.donor_name}</strong>
                        <p style={{ fontSize: '14px', color: '#6b7280', margin: '5px 0' }}>
                          {donor.donor_blood_group} | {donor.donor_phone}
                        </p>
                        {donor.distance_km && (
                          <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                            Distance: {donor.distance_km.toFixed(2)} km
                          </p>
                        )}
                      </div>
                      <button
                        className="btn btn-success"
                        style={{ fontSize: '13px', padding: '8px 16px' }}
                        onClick={() => handleConfirmFulfillment(donor.donor_id, 'donor')}
                      >
                        Select
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#6b7280', fontStyle: 'italic', marginBottom: '20px' }}>
                No donors have accepted this request yet.
              </p>
            )}
            
            <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '20px', marginTop: '20px' }}>
              <button
                className="btn btn-secondary"
                style={{ width: '100%', marginBottom: '10px' }}
                onClick={() => handleConfirmFulfillment(null, 'other')}
              >
                Blood from Other Source
              </button>
              <button
                className="btn"
                style={{ width: '100%', backgroundColor: '#6b7280', color: 'white' }}
                onClick={() => {
                  setShowFulfillmentModal(false);
                  setAcceptedDonors([]);
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    
    {/* Notification Sidebar */}
    <NotificationSidebar />
    </div>
  );
};

export default RequesterDashboard;
