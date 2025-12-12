import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { locationAPI } from '../services/api';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component to handle map clicks
const MapClickHandler = ({ onLocationSelect }) => {
  useMapEvents({
    click: (e) => {
      onLocationSelect(e.latlng);
    },
  });
  return null;
};

const SavedLocations = () => {
  const [locations, setLocations] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [newLocation, setNewLocation] = useState({
    label: '',
    latitude: '',
    longitude: '',
    address: '',
    is_primary: false
  });
  
  useEffect(() => {
    loadLocations();
  }, []);
  
  const loadLocations = async () => {
    try {
      const response = await locationAPI.getMyLocations();
      setLocations(response.data);
    } catch (error) {
      console.error('Error loading locations:', error);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await locationAPI.createLocation({
        ...newLocation,
        latitude: parseFloat(newLocation.latitude),
        longitude: parseFloat(newLocation.longitude)
      });
      alert('Location added successfully!');
      setShowForm(false);
      setNewLocation({
        label: '',
        latitude: '',
        longitude: '',
        address: '',
        is_primary: false
      });
      loadLocations();
    } catch (error) {
      alert('Error adding location: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };
  
  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this location?')) {
      try {
        await locationAPI.deleteLocation(id);
        alert('Location deleted successfully!');
        loadLocations();
      } catch (error) {
        alert('Error deleting location: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    }
  };
  
  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position) => {
        setNewLocation(prev => ({
          ...prev,
          latitude: position.coords.latitude.toString(),
          longitude: position.coords.longitude.toString()
        }));
      });
    }
  };
  
  return (
    <div className="container">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Saved Locations</h2>
            <p style={{ color: '#6b7280', marginTop: '10px' }}>
              Manage your frequently used locations
            </p>
          </div>
          <button 
            className="btn btn-primary"
            onClick={() => setShowForm(!showForm)}
          >
            {showForm ? 'Cancel' : '+ Add Location'}
          </button>
        </div>
      </div>
      
      {showForm && (
        <div className="card">
          <h3 style={{ marginBottom: '15px' }}>Add New Location</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Label *</label>
              <input
                type="text"
                value={newLocation.label}
                onChange={(e) => setNewLocation({...newLocation, label: e.target.value})}
                placeholder="e.g., Home, Office, Gym"
                required
              />
            </div>
            
            <div className="grid grid-2">
              <div className="form-group">
                <label>Latitude *</label>
                <input
                  type="number"
                  step="any"
                  value={newLocation.latitude}
                  onChange={(e) => setNewLocation({...newLocation, latitude: e.target.value})}
                  required
                />
              </div>
              
              <div className="form-group">
                <label>Longitude *</label>
                <input
                  type="number"
                  step="any"
                  value={newLocation.longitude}
                  onChange={(e) => setNewLocation({...newLocation, longitude: e.target.value})}
                  required
                />
              </div>
            </div>
            
            <button 
              type="button"
              className="btn btn-secondary"
              onClick={getCurrentLocation}
              style={{ marginBottom: '15px' }}
            >
              📍 Use Current Location
            </button>
            
            <div className="form-group">
              <label>Address</label>
              <input
                type="text"
                value={newLocation.address}
                onChange={(e) => setNewLocation({...newLocation, address: e.target.value})}
                placeholder="Optional address description"
              />
            </div>
            
            {newLocation.latitude && newLocation.longitude && (
              <div className="form-group">
                <label>Click on map to adjust location</label>
                <div style={{ height: '300px', marginTop: '10px', borderRadius: '8px', overflow: 'hidden', border: '2px solid #e5e7eb' }}>
                  <MapContainer 
                    center={[parseFloat(newLocation.latitude) || 40.7128, parseFloat(newLocation.longitude) || -74.0060]} 
                    zoom={13} 
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />
                    <MapClickHandler 
                      onLocationSelect={(latlng) => {
                        setNewLocation(prev => ({
                          ...prev,
                          latitude: latlng.lat.toString(),
                          longitude: latlng.lng.toString()
                        }));
                      }}
                    />
                    <Marker position={[parseFloat(newLocation.latitude), parseFloat(newLocation.longitude)]}>
                      <Popup>{newLocation.label || 'New Location'}</Popup>
                    </Marker>
                  </MapContainer>
                </div>
                <small style={{ color: '#6b7280', marginTop: '5px', display: 'block' }}>
                  📍 Lat: {parseFloat(newLocation.latitude).toFixed(6)}, Lng: {parseFloat(newLocation.longitude).toFixed(6)}
                </small>
              </div>
            )}
            
            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center' }}>
                <input
                  type="checkbox"
                  checked={newLocation.is_primary}
                  onChange={(e) => setNewLocation({...newLocation, is_primary: e.target.checked})}
                  style={{ marginRight: '10px', width: 'auto' }}
                />
                Set as primary location
              </label>
            </div>
            
            <button type="submit" className="btn btn-primary">
              Add Location
            </button>
          </form>
        </div>
      )}
      
      <div className="card">
        <h3 style={{ marginBottom: '15px' }}>Your Locations</h3>
        {locations.length === 0 ? (
          <div className="empty-state">
            <h3>No saved locations</h3>
            <p>Add your first location to get started</p>
          </div>
        ) : (
          <div className="grid grid-2">
            {locations.map(location => (
              <div key={location.id} style={{ 
                padding: '20px', 
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
                border: location.is_primary ? '2px solid #dc2626' : 'none'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div>
                    <h4 style={{ marginBottom: '10px' }}>
                      {location.label}
                      {location.is_primary && (
                        <span className="badge badge-danger" style={{ marginLeft: '10px' }}>
                          Primary
                        </span>
                      )}
                    </h4>
                    <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                      {location.address || 'No address provided'}
                    </p>
                    <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                      📍 {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                    </p>
                  </div>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => handleDelete(location.id)}
                    style={{ padding: '5px 10px', fontSize: '12px' }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SavedLocations;
