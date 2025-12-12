import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const DirectionsMap = ({ startLat, startLng, endLat, endLng, startLabel, endLabel }) => {
  const [route, setRoute] = useState(null);
  const [distance, setDistance] = useState(null);
  const [duration, setDuration] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRoute();
  }, [startLat, startLng, endLat, endLng]);

  const fetchRoute = async () => {
    try {
      const apiKey = 'eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImI1ZDM4MTM3NjM2YjQxOTQ4NmQxMWM4NTI3MzAzNjI0IiwiaCI6Im11cm11cjY0In0=';
      const url = `https://api.openrouteservice.org/v2/directions/driving-car?api_key=${apiKey}&start=${startLng},${startLat}&end=${endLng},${endLat}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.features && data.features[0]) {
        const coords = data.features[0].geometry.coordinates;
        const routeCoords = coords.map(c => [c[1], c[0]]);
        setRoute(routeCoords);
        
        const properties = data.features[0].properties.segments[0];
        setDistance((properties.distance / 1000).toFixed(2)); // Convert to km
        setDuration((properties.duration / 60).toFixed(0)); // Convert to minutes
      }
    } catch (error) {
      console.error('Error fetching route:', error);
    } finally {
      setLoading(false);
    }
  };

  const openInGoogleMaps = () => {
    const url = `https://www.google.com/maps/dir/?api=1&origin=${startLat},${startLng}&destination=${endLat},${endLng}&travelmode=driving`;
    window.open(url, '_blank');
  };

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>Loading route...</div>;
  }

  return (
    <div>
      {distance && duration && (
        <div style={{
          padding: '15px',
          backgroundColor: '#eff6ff',
          borderRadius: '8px',
          marginBottom: '15px',
          border: '2px solid #3b82f6'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '14px', color: '#1e40af', marginBottom: '5px' }}>
                <strong>Route Information</strong>
              </div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1e3a8a' }}>
                {distance} km
              </div>
              <div style={{ fontSize: '14px', color: '#6b7280' }}>
                Estimated time: {duration} minutes
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

      <div style={{ height: '400px', borderRadius: '8px', overflow: 'hidden' }}>
        <MapContainer
          center={[(startLat + endLat) / 2, (startLng + endLng) / 2]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          />
          
          {/* Start marker */}
          <Marker 
            position={[startLat, startLng]}
            icon={L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
              shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
            })}
          >
            <Popup>
              <strong>{startLabel || 'Start'}</strong>
            </Popup>
          </Marker>
          
          {/* End marker */}
          <Marker 
            position={[endLat, endLng]}
            icon={L.icon({
              iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
              shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
              iconSize: [25, 41],
              iconAnchor: [12, 41],
            })}
          >
            <Popup>
              <strong>{endLabel || 'Destination'}</strong>
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

      <div style={{
        marginTop: '15px',
        padding: '10px',
        backgroundColor: '#f9fafb',
        borderRadius: '6px',
        fontSize: '12px',
        color: '#6b7280'
      }}>
        💡 <strong>Tip:</strong> Click "Open in Google Maps" for turn-by-turn navigation on your phone.
      </div>
    </div>
  );
};

export default DirectionsMap;
