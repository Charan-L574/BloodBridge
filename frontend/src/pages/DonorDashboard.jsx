import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import useAuthStore from '../store/authStore';
import { bloodRequestAPI, locationAPI, createWebSocket } from '../services/api';
import NotificationToast from '../components/NotificationToast';
import HealthCheckModal from '../components/HealthCheckModal';
import NotificationSidebar from '../components/NotificationSidebar';
import UniversalDirectionsModal from '../components/UniversalDirectionsModal';

const DonorDashboard = () => {
  const { user, token } = useAuthStore();
  const navigate = useNavigate();
  const [locations, setLocations] = useState([]);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showHealthModal, setShowHealthModal] = useState(false);
  const [selectedRequestId, setSelectedRequestId] = useState(null);
  // Load accepted requests from localStorage for persistence
  const [acceptedRequests, setAcceptedRequests] = useState(() => {
    const saved = localStorage.getItem('acceptedRequests');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });
  const [showDirectionsModal, setShowDirectionsModal] = useState(false);
  const [directionsRequest, setDirectionsRequest] = useState(null);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [locationLoading, setLocationLoading] = useState(false);
  const [notifications, setNotifications] = useState([]);
  
  useEffect(() => {
    loadData();
    
    // Setup WebSocket for real-time notifications
    if (!token) {
      console.log('❌ No token available for WebSocket connection');
      return;
    }
    
    console.log('🔌 Connecting to WebSocket with token...');
    const ws = createWebSocket(token);
    
    ws.onopen = () => {
      console.log('✅ DonorDashboard WebSocket connected');
    };
    
    ws.onerror = (error) => {
      console.error('❌ DonorDashboard WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('🔌 DonorDashboard WebSocket closed');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('🔔 DonorDashboard WebSocket message:', message);
      if (message.type === 'notification' && message.notification_type) {
        // Add notification to show toast
        console.log('✅ Adding notification to toast queue:', message);
        setNotifications(prev => {
          const newNotifications = [...prev, { ...message, id: Date.now() }];
          console.log('📋 Updated DonorDashboard notifications:', newNotifications);
          return newNotifications;
        });
        
        // Reload blood requests when new_blood_request notification arrives
        if (message.notification_type === 'new_blood_request') {
          console.log('🔄 Reloading blood requests due to new_blood_request notification');
          loadData();
        }
      }
    };
    
    return () => {
      console.log('🔌 Closing DonorDashboard WebSocket...');
      ws.close();
    };
  }, [token]);

  // Save acceptedRequests to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('acceptedRequests', JSON.stringify([...acceptedRequests]));
  }, [acceptedRequests]);
  
  const loadData = async () => {
    try {
      const [locationsRes, requestsRes] = await Promise.all([
        locationAPI.getMyLocations(),
        bloodRequestAPI.getRequests()
      ]);
      setLocations(locationsRes.data);
      // Filter pending requests
      const pendingRequests = requestsRes.data.filter(r => r.status === 'pending');
      console.log('📋 Loaded requests with matched location info:', pendingRequests);
      console.log('🔍 First request matched_location_label:', pendingRequests[0]?.matched_location_label);
      console.log('🔍 First request distance_from_matched_location:', pendingRequests[0]?.distance_from_matched_location);
      console.log('🔍 First request full data:', pendingRequests[0]);
      setRequests(pendingRequests);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get user's current location via browser geolocation
  const getCurrentLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => reject(error),
        { enableHighAccuracy: true, timeout: 10000 }
      );
    });
  };
  
  const handleAcceptRequest = (requestId) => {
    setSelectedRequestId(requestId);
    setShowHealthModal(true);
  };

  const handleHealthCheckSubmit = async (healthData) => {
    try {
      const primaryLocation = locations.find(l => l.is_primary);
      const response = await bloodRequestAPI.acceptRequest(selectedRequestId, {
        ...healthData,
        saved_location_id: primaryLocation?.id,
      });
      
      setShowHealthModal(false);
      
      if (response.data.is_eligible) {
        alert('✅ Request accepted! The requester will be notified with your contact details.');
        // Mark this request as accepted
        setAcceptedRequests(prev => new Set([...prev, selectedRequestId]));
      } else {
        const reasons = JSON.parse(response.data.eligibility_reasons || '[]');
        alert('❌ Request rejected due to health restrictions:\n\n' + reasons.join('\n'));
      }
      loadData();
    } catch (error) {
      alert('Error accepting request: ' + (error.response?.data?.detail || 'Unknown error'));
      setShowHealthModal(false);
    }
  };

  const handleShowDirections = async (request) => {
    console.log('🗺️ Show Directions clicked for request:', request);
    console.log('📍 Current locations:', locations);
    console.log('📍 Current location from browser:', currentLocation);
    
    setDirectionsRequest(request);
    setLocationLoading(true);
    
    // Try to get current location if no saved locations
    if (locations.length === 0 || !locations[0]) {
      try {
        const loc = await getCurrentLocation();
        console.log('✅ Got current location:', loc);
        setCurrentLocation(loc);
      } catch (error) {
        console.error('❌ Could not get current location:', error);
        alert('Please enable location access or save a location to see directions.');
        setLocationLoading(false);
        return;
      }
    }
    
    setLocationLoading(false);
    setShowDirectionsModal(true);
  };

  // Get start coordinates - use nearest location to the request
  const getStartCoordinates = () => {
    // If we have a request and saved locations, find the nearest one
    if (directionsRequest && directionsRequest.latitude && directionsRequest.longitude && locations.length > 0) {
      let nearestLoc = null;
      let minDistance = Infinity;
      
      for (const loc of locations) {
        if (loc.latitude && loc.longitude) {
          const R = 6371;
          const dLat = (directionsRequest.latitude - loc.latitude) * Math.PI / 180;
          const dLon = (directionsRequest.longitude - loc.longitude) * Math.PI / 180;
          const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(loc.latitude * Math.PI / 180) * Math.cos(directionsRequest.latitude * Math.PI / 180) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
          const distance = R * c;
          
          if (distance < minDistance) {
            minDistance = distance;
            nearestLoc = loc;
          }
        }
      }
      
      if (nearestLoc) {
        return {
          lat: nearestLoc.latitude,
          lng: nearestLoc.longitude,
          label: nearestLoc.label || 'Your Nearest Location'
        };
      }
    }
    
    // Fallback: Try primary location first
    const primaryLoc = locations.find(l => l.is_primary);
    if (primaryLoc && primaryLoc.latitude && primaryLoc.longitude) {
      return {
        lat: primaryLoc.latitude,
        lng: primaryLoc.longitude,
        label: primaryLoc.label || 'Your Primary Location'
      };
    }
    
    // Try any saved location
    if (locations.length > 0 && locations[0] && locations[0].latitude && locations[0].longitude) {
      return {
        lat: locations[0].latitude,
        lng: locations[0].longitude,
        label: locations[0].label || 'Your Saved Location'
      };
    }
    
    // Fallback to current location
    if (currentLocation && currentLocation.latitude && currentLocation.longitude) {
      return {
        lat: currentLocation.latitude,
        lng: currentLocation.longitude,
        label: 'Your Current Location'
      };
    }
    
    return null;
  };
  
  if (loading) {
    return <div className="loading">Loading...</div>;
  }
  
  return (
    <div style={{ display: 'flex', gap: '20px', width: '100%', padding: '20px', margin: '0', alignItems: 'flex-start' }}>
      <div style={{ flex: 1 }}>
      
      <div className="card">
        <h2>Donor Dashboard</h2>
        <p style={{ color: '#6b7280', marginTop: '10px' }}>
          Welcome, {user?.full_name}! Blood Group: <strong>{user?.blood_group}</strong>
        </p>
      </div>
      
      <div className="grid grid-2">
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>📍 My Saved Locations</h3>
          {locations.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No saved locations yet.</p>
          ) : (
            <div>
              {locations.map(loc => (
                <div key={loc.id} style={{ 
                  padding: '10px', 
                  backgroundColor: '#f9fafb', 
                  borderRadius: '4px',
                  marginBottom: '10px'
                }}>
                  <strong>{loc.label}</strong>
                  {loc.is_primary && <span className="badge badge-info" style={{ marginLeft: '10px' }}>Primary</span>}
                  <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '5px' }}>
                    {loc.address}
                  </p>
                </div>
              ))}
            </div>
          )}
          <button 
            className="btn btn-primary" 
            style={{ marginTop: '15px' }}
            onClick={() => navigate('/locations')}
          >
            Manage Locations
          </button>
        </div>
        
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>🩸 Pending Blood Requests</h3>
          {requests.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No pending requests at the moment.</p>
          ) : (
            <div>
              {/* Map showing all requests */}
              {requests.length > 0 && locations.length > 0 && (
                <div style={{ marginBottom: '20px' }}>
                  <h4 style={{ marginBottom: '10px', fontSize: '14px', color: '#374151' }}>📍 Requests Near You</h4>
                  <div className="map-container" style={{ height: '350px', borderRadius: '6px', overflow: 'hidden' }}>
                    <MapContainer
                      center={locations[0] ? [locations[0].latitude, locations[0].longitude] : [40.7128, -74.0060]}
                      zoom={12}
                      style={{ height: '100%', width: '100%' }}
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      />
                      
                      {/* Show donor's locations (blue markers) */}
                      {locations.map(loc => (
                        <Marker
                          key={`loc-${loc.id}`}
                          position={[loc.latitude, loc.longitude]}
                          icon={L.icon({
                            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                            shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                            iconSize: [25, 41],
                            iconAnchor: [12, 41],
                          })}
                        >
                          <Popup>
                            <strong>📍 Your Location: {loc.label}</strong>
                            <br />
                            {loc.is_primary && <span style={{ color: '#16a34a', fontWeight: 'bold' }}>✓ Primary</span>}
                          </Popup>
                        </Marker>
                      ))}
                      
                      {/* 6km radius circles around donor locations */}
                      {locations.map(loc => (
                        <Circle
                          key={`circle-${loc.id}`}
                          center={[loc.latitude, loc.longitude]}
                          radius={6000}
                          pathOptions={{ color: '#3b82f6', fillColor: '#dbeafe', fillOpacity: 0.1 }}
                        />
                      ))}
                      
                      {/* Show blood requests (red markers) */}
                      {requests.map(req => {
                        if (!req.latitude || !req.longitude) return null;
                        
                        // Calculate distance from donor's primary location
                        let minDistance = null;
                        if (locations.length > 0) {
                          const primaryLoc = locations.find(l => l.is_primary) || locations[0];
                          const R = 6371; // Earth's radius in km
                          const dLat = (req.latitude - primaryLoc.latitude) * Math.PI / 180;
                          const dLon = (req.longitude - primaryLoc.longitude) * Math.PI / 180;
                          const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                                  Math.cos(primaryLoc.latitude * Math.PI / 180) * Math.cos(req.latitude * Math.PI / 180) *
                                  Math.sin(dLon/2) * Math.sin(dLon/2);
                          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                          minDistance = (R * c).toFixed(2);
                        }
                        
                        return (
                          <Marker
                            key={`req-${req.id}`}
                            position={[req.latitude, req.longitude]}
                            icon={L.icon({
                              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                              shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                              iconSize: [25, 41],
                              iconAnchor: [12, 41],
                            })}
                          >
                            <Popup>
                              <strong>🩸 {req.blood_group} Blood Request</strong>
                              <br />
                              Urgency: {req.urgency_level}
                              <br />
                              Units: {req.units_needed}
                              <br />
                              {minDistance && `Distance: ${minDistance} km`}
                              <br />
                              <button
                                className="btn btn-primary"
                                style={{ marginTop: '5px', fontSize: '12px', padding: '4px 8px' }}
                                onClick={() => handleShowDirections(req)}
                              >
                                🗺️ Directions
                              </button>
                            </Popup>
                          </Marker>
                        );
                      })}
                    </MapContainer>
                  </div>
                </div>
              )}
              
              {requests.map(req => {
                // Use backend-provided distance or calculate from nearest location
                let distance = req.distance_from_matched_location;
                if (!distance && locations.length > 0 && req.latitude && req.longitude) {
                  // Find nearest location instead of using primary
                  let minDistance = Infinity;
                  for (const loc of locations) {
                    const R = 6371;
                    const dLat = (req.latitude - loc.latitude) * Math.PI / 180;
                    const dLon = (req.longitude - loc.longitude) * Math.PI / 180;
                    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                            Math.cos(loc.latitude * Math.PI / 180) * Math.cos(req.latitude * Math.PI / 180) *
                            Math.sin(dLon/2) * Math.sin(dLon/2);
                    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                    const dist = R * c;
                    if (dist < minDistance) {
                      minDistance = dist;
                    }
                  }
                  distance = minDistance.toFixed(2);
                }
                
                return (
                <div key={req.id} style={{ 
                  padding: '15px', 
                  backgroundColor: '#fef3c7', 
                  borderRadius: '4px',
                  marginBottom: '10px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div>
                      <strong style={{ fontSize: '16px' }}>{req.blood_group}</strong>
                      <span className="badge badge-warning" style={{ marginLeft: '10px' }}>
                        {req.urgency_level}
                      </span>
                      {distance && (
                        <span style={{ 
                          marginLeft: '10px', 
                          padding: '2px 8px', 
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}>
                          📍 {distance} km away
                        </span>
                      )}
                      <p style={{ fontSize: '14px', color: '#374151', marginTop: '8px', fontWeight: '500' }}>
                        👤 Requested by: {req.hospital_name || req.requester_name || 'Unknown'}
                      </p>
                      {req.requester_phone && (
                        <p style={{ fontSize: '14px', color: '#374151', marginTop: '4px', fontWeight: '500' }}>
                          📞 Contact: {req.requester_phone}
                        </p>
                      )}
                      {req.matched_location_label && (
                        <p style={{ 
                          fontSize: '13px', 
                          color: '#059669', 
                          marginTop: '6px', 
                          fontWeight: '600',
                          padding: '4px 8px',
                          backgroundColor: '#d1fae5',
                          borderRadius: '4px',
                          display: 'inline-block'
                        }}>
                          🎯 Matched to: {req.matched_location_label} ({req.distance_from_matched_location} km)
                        </p>
                      )}
                      <p style={{ fontSize: '14px', color: '#6b7280', marginTop: '4px' }}>
                        📍 {req.address || 'Location provided'}
                      </p>
                      <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                        {new Date(req.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  {acceptedRequests.has(req.id) ? (
                    <button 
                      className="btn btn-primary" 
                      style={{ marginTop: '10px', width: '100%' }}
                      onClick={() => handleShowDirections(req)}
                    >
                      🗺️ Show Directions
                    </button>
                  ) : (
                    <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                      <button 
                        className="btn btn-primary" 
                        style={{ flex: 1 }}
                        onClick={() => handleShowDirections(req)}
                      >
                        🗺️ View on Map
                      </button>
                      <button 
                        className="btn btn-success" 
                        style={{ flex: 1 }}
                        onClick={() => handleAcceptRequest(req.id)}
                      >
                        Accept & Respond
                      </button>
                    </div>
                  )}
                </div>
              )})}
            </div>
          )}
        </div>
      </div>
      
      <div className="card">
        <h3 style={{ marginBottom: '15px' }}>Quick Stats</h3>
        <div className="grid grid-3">
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
            <h2 style={{ color: '#dc2626' }}>{locations.length}</h2>
            <p style={{ color: '#6b7280' }}>Saved Locations</p>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
            <h2 style={{ color: '#dc2626' }}>{requests.length}</h2>
            <p style={{ color: '#6b7280' }}>Active Requests</p>
          </div>
          <div style={{ textAlign: 'center', padding: '20px', backgroundColor: '#f9fafb', borderRadius: '4px' }}>
            <h2 style={{ color: user?.is_available ? '#16a34a' : '#6b7280' }}>
              {user?.is_available ? 'Available' : 'Unavailable'}
            </h2>
            <p style={{ color: '#6b7280' }}>Donation Status</p>
          </div>
        </div>
      </div>

      {/* Health Check Modal */}
      <HealthCheckModal
        isOpen={showHealthModal}
        onClose={() => setShowHealthModal(false)}
        onSubmit={handleHealthCheckSubmit}
        requestId={selectedRequestId}
      />
      
      {/* Directions Modal */}
      {(() => {
        const startCoords = getStartCoordinates();
        console.log('🚀 Opening directions modal with:', {
          startCoords,
          endLocation: directionsRequest,
          isOpen: showDirectionsModal && !locationLoading
        });
        return (
          <UniversalDirectionsModal
            isOpen={showDirectionsModal && !locationLoading}
            onClose={() => setShowDirectionsModal(false)}
            startLocation={startCoords}
            endLocation={directionsRequest && directionsRequest.latitude && directionsRequest.longitude ? {
              lat: directionsRequest.latitude,
              lng: directionsRequest.longitude,
              label: directionsRequest.address || 'Request Location'
            } : null}
            title="Directions to Blood Request"
            description={directionsRequest ? (
              <div>
                <strong>Request Details:</strong>
                <div style={{ marginTop: '5px' }}>
                  Blood Group: <strong style={{ color: '#ef4444' }}>{directionsRequest.blood_group}</strong> • 
                  Units: {directionsRequest.units_needed} • 
                  Urgency: {directionsRequest.urgency_level}
                </div>
                {directionsRequest.address && (
                  <div style={{ marginTop: '5px' }}>
                    📍 {directionsRequest.address}
                  </div>
                )}
              </div>
            ) : null}
          />
        );
      })()}
      
      {locationLoading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '40px',
            borderRadius: '8px',
            textAlign: 'center',
            color: '#6b7280'
          }}>
            Getting your location...
          </div>
        </div>
      )}
      
      {/* Notification Toasts */}
      {console.log('🎨 DonorDashboard rendering toasts:', notifications)}
      {notifications.map((notif, index) => {
        console.log(`🎯 DonorDashboard mapping notification #${index}:`, notif);
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
    </div>
    
    {/* Notification Sidebar */}
    <NotificationSidebar />
    </div>
  );
};

export default DonorDashboard;
