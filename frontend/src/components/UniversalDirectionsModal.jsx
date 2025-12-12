import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const UniversalDirectionsModal = ({ 
  isOpen, 
  onClose, 
  startLocation, 
  endLocation, 
  title = "Directions",
  description 
}) => {
  const [route, setRoute] = useState(null);
  const [distance, setDistance] = useState(null);
  const [duration, setDuration] = useState(null);
  const [steps, setSteps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && startLocation && endLocation) {
      console.log('🗺️ Modal opened with locations:', { startLocation, endLocation });
      
      // Validate coordinates
      if (!startLocation.lat || !startLocation.lng || !endLocation.lat || !endLocation.lng) {
        console.error('❌ Invalid coordinates:', { startLocation, endLocation });
        setError('Invalid location coordinates. Please check your saved locations.');
        setLoading(false);
        return;
      }
      
      // Calculate straight-line distance instead of using routing API
      calculateStraightLineRoute();
    }
  }, [isOpen, startLocation, endLocation]);
  
  const calculateStraightLineRoute = () => {
    setLoading(true);
    setError(null);
    
    try {
      // Calculate distance using Haversine formula
      const R = 6371; // Earth's radius in km
      const dLat = (endLocation.lat - startLocation.lat) * Math.PI / 180;
      const dLon = (endLocation.lng - startLocation.lng) * Math.PI / 180;
      const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(startLocation.lat * Math.PI / 180) * Math.cos(endLocation.lat * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
      const distanceKm = R * c;
      
      // Estimate duration (assuming average speed of 30 km/h in city traffic)
      const durationMinutes = (distanceKm / 30) * 60;
      
      // Set route as straight line
      setRoute([[startLocation.lat, startLocation.lng], [endLocation.lat, endLocation.lng]]);
      setDistance(distanceKm.toFixed(2));
      setDuration(Math.round(durationMinutes));
      setSteps([]);
      
      console.log('✅ Route calculated:', { distance: distanceKm.toFixed(2), duration: Math.round(durationMinutes) });
    } catch (error) {
      console.error('❌ Error calculating route:', error);
      setError('Could not calculate route');
    } finally {
      setLoading(false);
    }
  };

  const openInGoogleMaps = () => {
    const url = `https://www.google.com/maps/dir/?api=1&origin=${startLocation.lat},${startLocation.lng}&destination=${endLocation.lat},${endLocation.lng}&travelmode=driving`;
    window.open(url, '_blank');
  };

  if (!isOpen) return null;

  return (
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
        padding: '20px',
        borderRadius: '8px',
        maxWidth: '900px',
        width: '90%',
        maxHeight: '90vh',
        overflow: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0 }}>🗺️ {title}</h3>
          <button
            onClick={onClose}
            style={{
              border: 'none',
              background: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#6b7280'
            }}
          >
            ×
          </button>
        </div>

        {description && (
          <div style={{ 
            marginBottom: '15px', 
            padding: '12px', 
            backgroundColor: '#fef3c7', 
            borderRadius: '6px',
            fontSize: '14px'
          }}>
            {description}
          </div>
        )}

        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: '#6b7280' }}>
            Loading directions...
          </div>
        ) : error ? (
          <div style={{ padding: '30px', textAlign: 'center' }}>
            <div style={{ color: '#ef4444', fontSize: '18px', fontWeight: '500', marginBottom: '10px' }}>
              {error}
            </div>
            <div style={{ color: '#6b7280', fontSize: '14px' }}>
              Please check your saved locations and try again.
            </div>
          </div>
        ) : (
          <>
            {distance && duration && (
              <div style={{
                padding: '15px',
                backgroundColor: '#eff6ff',
                borderRadius: '8px',
                marginBottom: '15px',
                border: '2px solid #3b82f6'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '15px' }}>
                  <div>
                    <div style={{ fontSize: '14px', color: '#1e40af', marginBottom: '5px' }}>
                      <strong>Route Information</strong>
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1e3a8a' }}>
                      {distance} km
                    </div>
                    <div style={{ fontSize: '14px', color: '#6b7280' }}>
                      ⏱️ Estimated time: {duration} minutes (30 km/h avg)
                    </div>
                    <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px', fontStyle: 'italic' }}>
                      * Straight-line distance shown. Click Google Maps for actual route.
                    </div>
                  </div>
                  <button
                    className="btn btn-primary"
                    onClick={openInGoogleMaps}
                    style={{ fontSize: '14px' }}
                  >
                    🗺️ Open in Google Maps
                  </button>
                </div>
              </div>
            )}

            <div style={{ height: '450px', borderRadius: '8px', overflow: 'hidden', border: '2px solid #e5e7eb' }}>
              <MapContainer
                center={[(startLocation.lat + endLocation.lat) / 2, (startLocation.lng + endLocation.lng) / 2]}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                />
                
                {/* Start marker */}
                <Marker 
                  position={[startLocation.lat, startLocation.lng]}
                  icon={L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                  })}
                >
                  <Popup>
                    <strong>📍 {startLocation.label || 'Start'}</strong>
                  </Popup>
                </Marker>
                
                {/* End marker */}
                <Marker 
                  position={[endLocation.lat, endLocation.lng]}
                  icon={L.icon({
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                  })}
                >
                  <Popup>
                    <strong>🎯 {endLocation.label || 'Destination'}</strong>
                  </Popup>
                </Marker>
                
                {/* Route polyline */}
                {route && (
                  <Polyline
                    positions={route}
                    pathOptions={{
                      color: '#3b82f6',
                      weight: 5,
                      opacity: 0.7
                    }}
                  />
                )}
              </MapContainer>
            </div>

            {/* Turn-by-turn navigation steps */}
            {steps && steps.length > 0 && (
              <div style={{ marginTop: '20px' }}>
                <h4 style={{ marginBottom: '15px', fontSize: '16px', color: '#1f2937' }}>
                  🧭 Turn-by-Turn Directions ({steps.length} steps)
                </h4>
                <div style={{ 
                  maxHeight: '300px', 
                  overflowY: 'auto', 
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  padding: '10px'
                }}>
                  {steps.map((step, index) => (
                    <div key={index} style={{
                      display: 'flex',
                      gap: '12px',
                      padding: '12px',
                      backgroundColor: 'white',
                      borderRadius: '6px',
                      marginBottom: '8px',
                      border: '1px solid #e5e7eb'
                    }}>
                      <div style={{
                        minWidth: '30px',
                        height: '30px',
                        borderRadius: '50%',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                        fontSize: '12px'
                      }}>
                        {index + 1}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '14px', color: '#1f2937', marginBottom: '4px' }}>
                          {step.instruction || 'Continue'}
                        </div>
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>
                          {(step.distance / 1000).toFixed(2)} km • {(step.duration / 60).toFixed(1)} min
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{
              marginTop: '15px',
              padding: '12px',
              backgroundColor: '#f0fdf4',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#166534',
              border: '1px solid #86efac'
            }}>
              💡 <strong>Tip:</strong> Click "Navigate with Google Maps" for turn-by-turn voice navigation on your device.
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default UniversalDirectionsModal;
