import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import { createWebSocket } from '../services/api';
import useAuthStore from '../store/authStore';

// Sample GPS route (simulated movement in NYC)
const SAMPLE_ROUTE = [
  [40.7128, -74.0060],  // Start
  [40.7138, -74.0050],
  [40.7148, -74.0040],
  [40.7158, -74.0030],
  [40.7168, -74.0020],
  [40.7178, -74.0010],
  [40.7188, -74.0000],  // End
];

const SimulateDonorMovement = () => {
  const { token } = useAuthStore();
  const [ws, setWs] = useState(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentPosition, setCurrentPosition] = useState(0);
  const [donorResponseId, setDonorResponseId] = useState('1');
  const [speed, setSpeed] = useState(2); // seconds between updates
  const [route, setRoute] = useState(SAMPLE_ROUTE);
  
  useEffect(() => {
    if (token && !ws) {
      const websocket = createWebSocket(token);
      
      websocket.onopen = () => {
        console.log('WebSocket connected for simulation');
      };
      
      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('Received:', message);
      };
      
      setWs(websocket);
      
      return () => {
        websocket.close();
      };
    }
  }, [token, ws]);
  
  const startSimulation = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      alert('WebSocket not connected. Please wait and try again.');
      return;
    }
    
    setIsSimulating(true);
    setCurrentPosition(0);
    
    let position = 0;
    const interval = setInterval(() => {
      if (position >= route.length) {
        clearInterval(interval);
        setIsSimulating(false);
        alert('Simulation complete!');
        return;
      }
      
      const [lat, lon] = route[position];
      
      // Send location update
      ws.send(JSON.stringify({
        type: 'location_update',
        data: {
          donor_response_id: parseInt(donorResponseId),
          latitude: lat,
          longitude: lon
        }
      }));
      
      console.log(`Sent location update: ${lat}, ${lon}`);
      setCurrentPosition(position);
      position++;
    }, speed * 1000);
  };
  
  const stopSimulation = () => {
    setIsSimulating(false);
    
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'stop_tracking',
        data: {
          donor_response_id: parseInt(donorResponseId)
        }
      }));
    }
  };
  
  const addCustomPoint = () => {
    const lat = parseFloat(prompt('Enter latitude:', '40.7128'));
    const lon = parseFloat(prompt('Enter longitude:', '-74.0060'));
    
    if (!isNaN(lat) && !isNaN(lon)) {
      setRoute([...route, [lat, lon]]);
    }
  };
  
  return (
    <div className="container">
      <div className="card">
        <h2>🚗 Simulate Donor Movement</h2>
        <p style={{ color: '#6b7280', marginTop: '10px' }}>
          This tool simulates a donor's GPS movement for testing real-time tracking features.
        </p>
      </div>
      
      <div className="grid grid-2">
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>Simulation Controls</h3>
          
          <div className="form-group">
            <label>Donor Response ID</label>
            <input
              type="number"
              value={donorResponseId}
              onChange={(e) => setDonorResponseId(e.target.value)}
              disabled={isSimulating}
              placeholder="Enter donor response ID"
            />
            <p style={{ fontSize: '12px', color: '#6b7280', marginTop: '5px' }}>
              Get this ID from the donor response after accepting a request
            </p>
          </div>
          
          <div className="form-group">
            <label>Speed (seconds between updates)</label>
            <input
              type="number"
              min="1"
              max="10"
              value={speed}
              onChange={(e) => setSpeed(parseInt(e.target.value))}
              disabled={isSimulating}
            />
          </div>
          
          <div style={{ marginTop: '20px' }}>
            <div className="alert alert-info">
              <strong>WebSocket Status:</strong> {ws?.readyState === WebSocket.OPEN ? '✅ Connected' : '❌ Disconnected'}
            </div>
          </div>
          
          <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
            {!isSimulating ? (
              <button 
                className="btn btn-primary"
                onClick={startSimulation}
                style={{ flex: 1 }}
              >
                ▶️ Start Simulation
              </button>
            ) : (
              <button 
                className="btn btn-secondary"
                onClick={stopSimulation}
                style={{ flex: 1 }}
              >
                ⏹️ Stop Simulation
              </button>
            )}
          </div>
          
          {isSimulating && (
            <div style={{ marginTop: '20px' }}>
              <div className="alert alert-success">
                <strong>Simulating Movement...</strong>
                <br />
                Position: {currentPosition + 1} / {route.length}
              </div>
            </div>
          )}
        </div>
        
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>Route Management</h3>
          
          <div style={{ marginBottom: '15px' }}>
            <strong>Current Route:</strong> {route.length} points
          </div>
          
          <div style={{ maxHeight: '200px', overflowY: 'auto', backgroundColor: '#f9fafb', padding: '10px', borderRadius: '4px', marginBottom: '15px' }}>
            {route.map((point, idx) => (
              <div key={idx} style={{ 
                fontSize: '12px', 
                padding: '5px',
                backgroundColor: idx === currentPosition && isSimulating ? '#fef3c7' : 'transparent',
                fontWeight: idx === currentPosition && isSimulating ? 'bold' : 'normal'
              }}>
                {idx + 1}. [{point[0].toFixed(4)}, {point[1].toFixed(4)}]
              </div>
            ))}
          </div>
          
          <button 
            className="btn btn-secondary"
            onClick={addCustomPoint}
            disabled={isSimulating}
            style={{ width: '100%', marginBottom: '10px' }}
          >
            ➕ Add Custom Point
          </button>
          
          <button 
            className="btn btn-secondary"
            onClick={() => setRoute(SAMPLE_ROUTE)}
            disabled={isSimulating}
            style={{ width: '100%' }}
          >
            🔄 Reset to Default Route
          </button>
        </div>
      </div>
      
      <div className="card">
        <h3 style={{ marginBottom: '15px' }}>📍 Route Visualization</h3>
        <div className="map-container">
          <MapContainer
            center={route[0]}
            zoom={13}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {/* Start marker */}
            <Marker position={route[0]}>
              <Popup>
                <strong>Start Point</strong>
              </Popup>
            </Marker>
            
            {/* End marker */}
            <Marker position={route[route.length - 1]}>
              <Popup>
                <strong>End Point</strong>
              </Popup>
            </Marker>
            
            {/* Current position marker */}
            {isSimulating && currentPosition < route.length && (
              <Marker
                position={route[currentPosition]}
                icon={L.icon({
                  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
                  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                  iconSize: [25, 41],
                  iconAnchor: [12, 41],
                })}
              >
                <Popup>
                  <strong>Current Position</strong>
                  <br />
                  Point {currentPosition + 1} of {route.length}
                </Popup>
              </Marker>
            )}
            
            {/* Route line */}
            <Polyline
              positions={route}
              pathOptions={{ color: '#dc2626', weight: 3, opacity: 0.7 }}
            />
            
            {/* Traveled path (if simulating) */}
            {isSimulating && currentPosition > 0 && (
              <Polyline
                positions={route.slice(0, currentPosition + 1)}
                pathOptions={{ color: '#16a34a', weight: 4, opacity: 0.8 }}
              />
            )}
          </MapContainer>
        </div>
      </div>
      
      <div className="card">
        <h3 style={{ marginBottom: '15px' }}>📝 How to Use</h3>
        <ol style={{ paddingLeft: '20px', color: '#6b7280', lineHeight: '1.8' }}>
          <li>First, accept a blood request as a donor (with live tracking enabled)</li>
          <li>Note the <strong>donor_response_id</strong> from the response</li>
          <li>Enter that ID in the "Donor Response ID" field above</li>
          <li>Customize the route if needed (or use default)</li>
          <li>Click "Start Simulation" to begin sending location updates</li>
          <li>Open the requester's dashboard to see real-time tracking on the map</li>
          <li>The green marker will move along the route in real-time</li>
        </ol>
        
        <div className="alert alert-info" style={{ marginTop: '20px' }}>
          <strong>💡 Tip:</strong> Keep this page open alongside the requester's dashboard 
          to see the live tracking in action!
        </div>
      </div>
    </div>
  );
};

export default SimulateDonorMovement;
