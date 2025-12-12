import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { bloodRequestAPI, locationAPI } from '../services/api';
import useAuthStore from '../store/authStore';
import UniversalDirectionsModal from '../components/UniversalDirectionsModal';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const MapView = () => {
  const { user } = useAuthStore();
  const [requests, setRequests] = useState([]);
  const [myLocations, setMyLocations] = useState([]);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [showDirectionsModal, setShowDirectionsModal] = useState(false);
  const [directionsData, setDirectionsData] = useState(null);
  const [mapCenter, setMapCenter] = useState([40.7128, -74.0060]); // Default to NYC
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    getUserLocation();
  }, []);

  const getUserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = [position.coords.latitude, position.coords.longitude];
          setCurrentLocation(coords);
          setMapCenter(coords);
        },
        (error) => {
          console.log('Could not get location:', error);
        }
      );
    }
  };

  const loadData = async () => {
    try {
      const [requestsRes, locationsRes] = await Promise.all([
        bloodRequestAPI.getRequests().catch(() => ({ data: [] })),
        locationAPI.getMyLocations().catch(() => ({ data: [] }))
      ]);
      
      setRequests(requestsRes.data || []);
      setMyLocations(locationsRes.data || []);
      
      // Set map center to first saved location if available
      if (locationsRes.data && locationsRes.data.length > 0) {
        setMapCenter([locationsRes.data[0].latitude, locationsRes.data[0].longitude]);
      }
    } catch (error) {
      console.error('Error loading map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNavigateToRequest = (request) => {
    const start = currentLocation || (myLocations.length > 0 
      ? [myLocations[0].latitude, myLocations[0].longitude] 
      : null);
    
    if (!start) {
      alert('Please enable location access or save a location first');
      return;
    }

    setDirectionsData({
      start: {
        lat: start[0],
        lng: start[1],
        label: currentLocation ? 'Your Current Location' : myLocations[0].label
      },
      end: {
        lat: request.latitude,
        lng: request.longitude,
        label: `${request.blood_group} Request`
      },
      title: `Navigate to Blood Request`,
      description: (
        <div>
          <strong>Request Details:</strong>
          <div style={{ marginTop: '5px' }}>
            Blood Group: <strong style={{ color: '#ef4444' }}>{request.blood_group}</strong> • 
            Units: {request.units_needed} • 
            Urgency: {request.urgency_level}
          </div>
          {request.address && (
            <div style={{ marginTop: '5px' }}>
              📍 {request.address}
            </div>
          )}
        </div>
      )
    });
    setShowDirectionsModal(true);
  };

  if (loading) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          Loading map...
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="card">
        <h2>📍 Interactive Map</h2>
        <p style={{ color: '#6b7280', marginTop: '10px' }}>
          View blood requests and navigate to locations
        </p>
      </div>

      <div className="card">
        <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap' }}>
          <div style={{ 
            flex: 1, 
            minWidth: '150px',
            padding: '10px', 
            backgroundColor: '#fef2f2', 
            borderRadius: '6px',
            border: '2px solid #ef4444'
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc2626' }}>
              {requests.filter(r => r.status === 'pending').length}
            </div>
            <div style={{ fontSize: '12px', color: '#991b1b' }}>Active Requests</div>
          </div>
          
          <div style={{ 
            flex: 1, 
            minWidth: '150px',
            padding: '10px', 
            backgroundColor: '#eff6ff', 
            borderRadius: '6px',
            border: '2px solid #3b82f6'
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1e40af' }}>
              {myLocations.length}
            </div>
            <div style={{ fontSize: '12px', color: '#1e3a8a' }}>Saved Locations</div>
          </div>
          
          <div style={{ 
            flex: 1, 
            minWidth: '150px',
            padding: '10px', 
            backgroundColor: '#f0fdf4', 
            borderRadius: '6px',
            border: '2px solid #10b981'
          }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#047857' }}>
              {currentLocation ? '✓' : '✗'}
            </div>
            <div style={{ fontSize: '12px', color: '#065f46' }}>GPS Available</div>
          </div>
        </div>

        <div style={{ height: '600px', borderRadius: '8px', overflow: 'hidden', border: '2px solid #e5e7eb' }}>
          <MapContainer
            center={mapCenter}
            zoom={12}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            />

            {/* Current Location */}
            {currentLocation && (
              <Marker 
                position={currentLocation}
                icon={L.icon({
                  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                  iconSize: [25, 41],
                  iconAnchor: [12, 41],
                })}
              >
                <Popup>
                  <strong>📍 Your Current Location</strong>
                </Popup>
              </Marker>
            )}

            {/* Saved Locations */}
            {myLocations.map((loc) => (
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
                  <strong>{loc.label}</strong>
                  {loc.is_primary && <span className="badge badge-info"> Primary</span>}
                  <br />
                  {loc.address}
                </Popup>
              </Marker>
            ))}

            {/* Blood Requests */}
            {requests
              .filter(r => r.status === 'pending')
              .map((request) => (
                <React.Fragment key={`req-${request.id}`}>
                  <Marker
                    position={[request.latitude, request.longitude]}
                    icon={L.icon({
                      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                      iconSize: [25, 41],
                      iconAnchor: [12, 41],
                    })}
                  >
                    <Popup>
                      <div style={{ minWidth: '200px' }}>
                        <strong style={{ fontSize: '16px', color: '#dc2626' }}>
                          {request.blood_group}
                        </strong>
                        <span className={`badge badge-${request.urgency_level === 'critical' ? 'danger' : 'warning'}`} style={{ marginLeft: '5px' }}>
                          {request.urgency_level}
                        </span>
                        <div style={{ marginTop: '8px', fontSize: '13px' }}>
                          Units: {request.units_needed}
                        </div>
                        {request.address && (
                          <div style={{ marginTop: '4px', fontSize: '12px', color: '#6b7280' }}>
                            📍 {request.address}
                          </div>
                        )}
                        <button
                          className="btn btn-primary"
                          style={{ marginTop: '10px', width: '100%', fontSize: '12px', padding: '6px' }}
                          onClick={() => handleNavigateToRequest(request)}
                        >
                          🗺️ Navigate Here
                        </button>
                      </div>
                    </Popup>
                  </Marker>
                  
                  {/* Radius circle around request */}
                  <Circle
                    center={[request.latitude, request.longitude]}
                    radius={5000} // 5km radius
                    pathOptions={{
                      color: request.urgency_level === 'critical' ? '#dc2626' : '#f59e0b',
                      fillColor: request.urgency_level === 'critical' ? '#fee2e2' : '#fef3c7',
                      fillOpacity: 0.15,
                      weight: 2
                    }}
                  />
                </React.Fragment>
              ))}
          </MapContainer>
        </div>

        <div style={{ marginTop: '15px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#10b981', borderRadius: '50%' }}></div>
            <span style={{ fontSize: '13px', color: '#6b7280' }}>Your Location</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#3b82f6', borderRadius: '50%' }}></div>
            <span style={{ fontSize: '13px', color: '#6b7280' }}>Saved Locations</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#ef4444', borderRadius: '50%' }}></div>
            <span style={{ fontSize: '13px', color: '#6b7280' }}>Blood Requests</span>
          </div>
        </div>
      </div>

      {/* Directions Modal */}
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
    </div>
  );
};

export default MapView;
