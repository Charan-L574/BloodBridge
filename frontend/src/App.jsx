import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import Navbar from './components/Navbar';
import PrivateRoute from './components/PrivateRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import DonorDashboard from './pages/DonorDashboard';
import RequesterDashboard from './pages/RequesterDashboard';
import ProfileEdit from './pages/ProfileEdit';
import MapView from './pages/MapView';
import NotificationsPage from './pages/NotificationsPage';
import BloodDemandForecast from './pages/BloodDemandForecast';
import DonationHistoryPage from './pages/DonationHistoryPage';
import QuickStatsPage from './pages/QuickStatsPage';
import './App.css';

const Dashboard = () => {
  const { user } = useAuthStore();
  
  if (!user) return <div className="loading">Loading...</div>;
  
  // Route to appropriate dashboard based on role
  if (user.role === 'donor') {
    return <DonorDashboard />;
  } else if (user.role === 'requester' || user.role === 'hospital') {
    return <RequesterDashboard />;
  } else {
    return <div className="container">
      <div className="card">
        <h2>Admin Dashboard</h2>
        <p>Admin features coming soon...</p>
      </div>
    </div>;
  }
};

function App() {
  const { isAuthenticated, loadUser } = useAuthStore();
  
  useEffect(() => {
    if (isAuthenticated) {
      loadUser();
    }
  }, [isAuthenticated, loadUser]);
  
  return (
    <Router>
      <div className="App">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route 
            path="/dashboard" 
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/profile" 
            element={
              <PrivateRoute>
                <ProfileEdit />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/map" 
            element={
              <PrivateRoute>
                <MapView />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/notifications" 
            element={
              <PrivateRoute>
                <NotificationsPage />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/demand-forecast" 
            element={
              <PrivateRoute>
                <BloodDemandForecast />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/donation-history" 
            element={
              <PrivateRoute>
                <DonationHistoryPage />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/quick-stats" 
            element={
              <PrivateRoute>
                <QuickStatsPage />
              </PrivateRoute>
            } 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
