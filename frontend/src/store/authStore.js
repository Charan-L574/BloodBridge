import { create } from 'zustand';
import { authAPI } from '../services/api';

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (email, password) => {
    try {
      console.log('Attempting login with:', email);
      const response = await authAPI.login(email, password);
      console.log('Login response:', response);
      const { access_token } = response.data;
      
      if (!access_token) {
        console.error('No access token in response');
        return { success: false, error: 'No access token received' };
      }
      
      localStorage.setItem('token', access_token);
      
      // Get user profile
      console.log('Fetching user profile...');
      try {
        const userResponse = await authAPI.getMe();
        console.log('User profile:', userResponse.data);
        
        set({ 
          token: access_token, 
          user: userResponse.data,
          isAuthenticated: true 
        });
        
        console.log('Login successful!');
        return { success: true };
      } catch (profileError) {
        console.error('Failed to fetch profile, but login succeeded:', profileError);
        // Even if profile fetch fails, login was successful
        set({ 
          token: access_token, 
          user: null,
          isAuthenticated: true 
        });
        return { success: true };
      }
    } catch (error) {
      console.error('Login error:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response,
        status: error.response?.status
      });
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Network Error - Cannot connect to server' 
      };
    }
  },
  
  register: async (data) => {
    try {
      await authAPI.register(data);
      // After registration, auto-login
      return await useAuthStore.getState().login(data.email, data.password);
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  loadUser: async () => {
    try {
      const response = await authAPI.getMe();
      set({ user: response.data });
    } catch (error) {
      // If loading user fails, clear auth
      useAuthStore.getState().logout();
    }
  },
  
  setToken: (token) => {
    localStorage.setItem('token', token);
    set({ token, isAuthenticated: true });
  },
}));

export default useAuthStore;
