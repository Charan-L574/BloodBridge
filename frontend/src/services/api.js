import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMe: () => api.get('/auth/me'),
  updateProfile: (data) => api.put('/auth/me', data),
  switchRole: (newRole) => api.post(`/auth/switch-role?new_role=${newRole}`),
};

// Location APIs
export const locationAPI = {
  createLocation: (data) => api.post('/locations', data),
  getMyLocations: () => api.get('/locations'),
  deleteLocation: (id) => api.delete(`/locations/${id}`),
  updateVisibilityMode: (mode) => api.put('/locations/visibility-mode', null, {
    params: { visibility_mode: mode }
  }),
};

// Blood Request APIs
export const bloodRequestAPI = {
  createRequest: (data) => api.post('/blood-requests', data),
  getRequests: (status) => api.get('/blood-requests', { params: { status } }),
  getRequest: (id) => api.get(`/blood-requests/${id}`),
  findMatchingDonors: (id, radius) => api.get(`/blood-requests/${id}/matching-donors`, {
    params: { radius_km: radius }
  }),
  acceptRequest: (id, data) => api.post(`/blood-requests/${id}/accept`, data),
  getResponses: (id) => api.get(`/blood-requests/${id}/responses`),
  updateStatus: (id, status, fulfilledByDonorId = null, fulfillmentSource = null) => api.put(`/blood-requests/${id}/status`, null, {
    params: { 
      new_status: status,
      fulfilled_by_donor_id: fulfilledByDonorId,
      fulfillment_source: fulfillmentSource
    }
  }),
  getAcceptedDonors: (id) => api.get(`/blood-requests/${id}/accepted-donors`),
  getDonationHistory: (limit = 50) => api.get('/blood-requests/history/donations', {
    params: { limit }
  }),
  getDemandForecast: (days = 7) => api.get('/blood-requests/forecast/demand', {
    params: { days }
  }),
};

// Hospital APIs
export const hospitalAPI = {
  createOrUpdateInventory: (data) => api.post('/hospital-inventory', data),
  getMyInventory: () => api.get('/hospital-inventory'),
  getAllInventory: (bloodGroup) => api.get('/hospital-inventory/all', {
    params: { blood_group: bloodGroup }
  }),
  getExpiringSoon: (days = 7) => api.get('/hospital-inventory/expiring-soon', {
    params: { days }
  }),
};

// Notification APIs
export const notificationAPI = {
  getNotifications: () => api.get('/notifications'),
  markAsRead: (id) => api.put(`/notifications/${id}/read`),
  deleteNotification: (id) => api.delete(`/notifications/${id}`),
};

// WebSocket connection
export const createWebSocket = (token) => {
  return new WebSocket(`ws://localhost:8000/ws?token=${token}`);
};

export default api;
