import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import { authAPI, locationAPI } from '../services/api';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

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

const ProfileEdit = () => {
  const { user, loadUser } = useAuthStore();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [locations, setLocations] = useState([]);
  const [showLocationForm, setShowLocationForm] = useState(false);
  const [newLocation, setNewLocation] = useState({
    label: '',
    latitude: '',
    longitude: '',
    address: '',
    is_primary: false
  });
  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    age: '',
    weight: '',
    is_available: true,
    visibility_mode: 'both',
    blood_group: '',
    hospital_name: '',
    hospital_address: ''
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        phone: user.phone || '',
        age: user.age || '',
        weight: user.weight || '',
        is_available: user.is_available ?? true,
        visibility_mode: user.visibility_mode || 'both',
        blood_group: user.blood_group || '',
        hospital_name: user.hospital_name || '',
        hospital_address: user.hospital_address || ''
      });
      loadLocations();
    }
  }, [user]);

  const loadLocations = async () => {
    try {
      const response = await locationAPI.getMyLocations();
      setLocations(response.data);
    } catch (error) {
      console.error('Error loading locations:', error);
    }
  };

  const handleLocationSubmit = async (e) => {
    e.preventDefault();
    try {
      await locationAPI.createLocation({
        ...newLocation,
        latitude: parseFloat(newLocation.latitude),
        longitude: parseFloat(newLocation.longitude)
      });
      alert('✅ Location added successfully!');
      setShowLocationForm(false);
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

  const handleDeleteLocation = async (id) => {
    if (window.confirm('Delete this location?')) {
      try {
        await locationAPI.deleteLocation(id);
        alert('✅ Location deleted!');
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
          latitude: position.coords.latitude.toFixed(6),
          longitude: position.coords.longitude.toFixed(6)
        }));
      });
    } else {
      alert('Geolocation is not supported by your browser');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Update profile
      await authAPI.updateProfile(formData);
      
      // Update visibility mode separately if donor
      if (user.role === 'donor') {
        await locationAPI.updateVisibilityMode(formData.visibility_mode);
      }

      await loadUser();
      alert('✅ Profile updated successfully!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Update error:', error);
      alert('Error updating profile: ' + (error.response?.data?.detail || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const getDaysSinceLastDonation = () => {
    if (!user?.last_donation_date) return null;
    const lastDonation = new Date(user.last_donation_date);
    const now = new Date();
    const diffTime = Math.abs(now - lastDonation);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const canDonateAgain = () => {
    const daysSince = getDaysSinceLastDonation();
    if (daysSince === null) return { can: true, message: 'Never donated before' };
    
    const daysRemaining = Math.max(0, 180 - daysSince);
    if (daysRemaining > 0) {
      return { 
        can: false, 
        message: `Must wait ${daysRemaining} more days (donated ${daysSince} days ago)` 
      };
    }
    return { can: true, message: 'Eligible to donate' };
  };

  return (
    <div className="container">
      <div className="card">
        <h2>Edit Profile</h2>
        
        {/* User Info Display */}
        <div style={{ 
          background: '#f3f4f6', 
          padding: '15px', 
          borderRadius: '8px', 
          marginBottom: '20px',
          fontSize: '14px'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <strong>Email:</strong> {user?.email}
            </div>
            <div>
              <strong>Role:</strong> {user?.role?.toUpperCase()}
            </div>
            {user?.blood_group && (
              <div>
                <strong>Blood Group:</strong> {user.blood_group}
              </div>
            )}
            {user?.timezone && (
              <div>
                <strong>Timezone:</strong> {user.timezone}
              </div>
            )}
            {user?.last_donation_date && (
              <>
                <div>
                  <strong>Last Donation:</strong> {formatDate(user.last_donation_date)}
                </div>
                <div>
                  <strong>Donation Status:</strong>{' '}
                  <span style={{ 
                    color: canDonateAgain().can ? '#10b981' : '#ef4444',
                    fontWeight: 'bold'
                  }}>
                    {canDonateAgain().message}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
        
        <form onSubmit={handleSubmit}>
          {/* Basic Info */}
          <div className="form-group">
            <label>Full Name *</label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Phone *</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Blood Group</label>
            <select
              name="blood_group"
              value={formData.blood_group}
              onChange={handleChange}
            >
              <option value="">Select Blood Group</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
            </select>
            <small>Required to switch to donor role</small>
          </div>

          <div className="form-group">
            <label>Age</label>
            <input
              type="number"
              name="age"
              value={formData.age}
              onChange={handleChange}
              min="18"
              max="65"
              placeholder="18-65 years"
            />
            <small>Must be 18-65 years to become a donor</small>
          </div>

          <div className="form-group">
            <label>Weight (kg)</label>
            <input
              type="number"
              name="weight"
              value={formData.weight}
              onChange={handleChange}
              step="0.1"
              min="50"
              placeholder="Minimum 50 kg"
            />
            <small>Must be at least 50 kg to become a donor</small>
          </div>

          {/* Donor Settings */}
          <div style={{ 
            background: '#eff6ff', 
            border: '1px solid #3b82f6',
            padding: '15px', 
            borderRadius: '8px', 
            marginTop: '20px',
            marginBottom: '15px'
          }}>
            <h3 style={{ marginTop: 0, fontSize: '16px', color: '#1e40af' }}>
              🩸 Donor Preferences
            </h3>
            
            <div className="form-group">
              <label>Location Sharing Preference</label>
              <select
                name="visibility_mode"
                value={formData.visibility_mode}
                onChange={handleChange}
              >
                <option value="saved_only">📍 Saved Locations Only - No live GPS tracking</option>
                <option value="live_only">🔴 Live Location Only - Share GPS when accepting</option>
                <option value="both">🔄 Both - Choose each time when accepting</option>
              </select>
            </div>

            <div className="form-group">
              <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <input
                  type="checkbox"
                  name="is_available"
                  checked={formData.is_available}
                  onChange={handleChange}
                  style={{ width: 'auto' }}
                />
                <span>Available for Donations</span>
              </label>
              <small>Uncheck if you're temporarily unable to donate</small>
            </div>
          </div>

          {/* Saved Locations Section */}
          <div style={{
            marginTop: '25px',
            padding: '20px',
            border: '1px solid #e5e7eb',
            borderRadius: '10px',
            background: 'white'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '15px'
            }}>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#1e40af' }}>
                📍 Saved Locations
              </h3>
              <button
                type="button"
                onClick={() => setShowLocationForm(!showLocationForm)}
                className="btn"
                style={{ 
                  padding: '8px 16px',
                  background: showLocationForm ? '#6b7280' : '#1e40af',
                  fontSize: '14px'
                }}
              >
                {showLocationForm ? 'Cancel' : '+ Add Location'}
              </button>
            </div>

            {showLocationForm && (
              <div style={{
                padding: '15px',
                background: '#f9fafb',
                borderRadius: '8px',
                marginBottom: '15px'
              }}>
                <h4 style={{ marginTop: 0, fontSize: '14px', color: '#374151' }}>Add New Location</h4>
                <div style={{ display: 'grid', gap: '12px' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label style={{ fontSize: '13px' }}>Location Label</label>
                    <input
                      type="text"
                      placeholder="e.g., Home, Office, Hospital"
                      value={newLocation.label}
                      onChange={(e) => setNewLocation({...newLocation, label: e.target.value})}
                      required
                    />
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontSize: '13px' }}>Latitude</label>
                      <input
                        type="number"
                        step="any"
                        placeholder="e.g., 13.0827"
                        value={newLocation.latitude}
                        onChange={(e) => setNewLocation({...newLocation, latitude: e.target.value})}
                        required
                      />
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontSize: '13px' }}>Longitude</label>
                      <input
                        type="number"
                        step="any"
                        placeholder="e.g., 80.2707"
                        value={newLocation.longitude}
                        onChange={(e) => setNewLocation({...newLocation, longitude: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label style={{ fontSize: '13px' }}>Address</label>
                    <input
                      type="text"
                      placeholder="Enter full address"
                      value={newLocation.address}
                      onChange={(e) => setNewLocation({...newLocation, address: e.target.value})}
                      required
                    />
                  </div>

                  {/* Interactive Map */}
                  {newLocation.latitude && newLocation.longitude && (
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label style={{ fontSize: '13px' }}>📍 Click on map to adjust location</label>
                      <div style={{ 
                        height: '300px', 
                        marginTop: '10px', 
                        borderRadius: '8px', 
                        overflow: 'hidden', 
                        border: '2px solid #e5e7eb' 
                      }}>
                        <MapContainer 
                          center={[
                            parseFloat(newLocation.latitude) || 13.0827, 
                            parseFloat(newLocation.longitude) || 80.2707
                          ]} 
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
                          <Marker position={[
                            parseFloat(newLocation.latitude), 
                            parseFloat(newLocation.longitude)
                          ]}>
                            <Popup>{newLocation.label || 'New Location'}</Popup>
                          </Marker>
                        </MapContainer>
                      </div>
                      <small style={{ 
                        color: '#6b7280', 
                        marginTop: '5px', 
                        display: 'block',
                        fontSize: '12px'
                      }}>
                        📍 Lat: {parseFloat(newLocation.latitude).toFixed(6)}, Lng: {parseFloat(newLocation.longitude).toFixed(6)}
                      </small>
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                    <button
                      type="button"
                      onClick={getCurrentLocation}
                      className="btn"
                      style={{ 
                        padding: '8px 12px',
                        background: '#10b981',
                        fontSize: '13px',
                        flex: 1
                      }}
                    >
                      📍 Use Current Location
                    </button>
                    
                    <label style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      fontSize: '13px',
                      margin: 0,
                      flex: 1
                    }}>
                      <input
                        type="checkbox"
                        checked={newLocation.is_primary}
                        onChange={(e) => setNewLocation({...newLocation, is_primary: e.target.checked})}
                        style={{ width: 'auto' }}
                      />
                      <span>Set as primary location</span>
                    </label>
                  </div>

                  <button
                    type="button"
                    onClick={handleLocationSubmit}
                    className="btn btn-primary"
                    style={{ padding: '10px', fontSize: '14px' }}
                  >
                    Save Location
                  </button>
                </div>
              </div>
            )}

            {/* Locations List */}
            <div>
              {locations.length === 0 ? (
                <p style={{ 
                  textAlign: 'center', 
                  color: '#6b7280', 
                  fontSize: '14px',
                  padding: '20px'
                }}>
                  No saved locations yet. Add your first location above.
                </p>
              ) : (
                <div style={{ display: 'grid', gap: '10px' }}>
                  {locations.map(location => (
                    <div
                      key={location.id}
                      style={{
                        padding: '12px',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                        background: location.is_primary ? '#eff6ff' : '#fff',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'start'
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <div style={{ 
                          fontWeight: 'bold', 
                          color: '#1f2937',
                          marginBottom: '4px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px'
                        }}>
                          {location.label}
                          {location.is_primary && (
                            <span style={{
                              fontSize: '11px',
                              padding: '2px 8px',
                              background: '#1e40af',
                              color: 'white',
                              borderRadius: '4px'
                            }}>
                              PRIMARY
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>
                          {location.address}
                        </div>
                        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                          📍 {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteLocation(location.id)}
                        style={{
                          padding: '6px 12px',
                          background: '#ef4444',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
            <button 
              type="button" 
              className="btn"
              onClick={() => navigate('/dashboard')}
              style={{ background: '#6b7280' }}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfileEdit;
