# 🩸 BloodBridge

Real-time blood donation platform connecting donors with emergency requests through intelligent matching and live tracking.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB.svg)](https://www.python.org)

## 🎯 Overview

BloodBridge is a comprehensive blood donation management system that enables real-time communication between blood donors and requesters. It uses intelligent ML-based matching algorithms, live location tracking, and WebSocket technology to facilitate quick and efficient emergency blood requests.

## ✨ Key Features

### 🔐 Multi-Role Authentication System
- **Donor**: Register to donate blood, manage availability, track donation history
- **Requester**: Create emergency blood requests, view matching donors
- **Hospital**: Manage blood inventory, create requests, track demand
- **Role Switching**: Donors and requesters can switch roles seamlessly

### 🩸 Blood Request Management
- Create emergency blood requests with urgency levels (Low, Medium, High, Critical)
- Automatic blood group compatibility matching (e.g., O- is universal donor)
- Real-time notifications to eligible donors within configurable radius
- Request status tracking (Pending, Fulfilled, Cancelled)
- Donor response management (Accept/Decline)

### 📍 Smart Location & Matching
- **Multi-Location Support**: Donors can save multiple locations (Home, Office, Custom)
- **Visibility Modes**:
  - Saved Only: Share only predefined locations
  - Live Only: Share real-time GPS location
  - Both: Share saved and live locations
- **Distance-Based Matching**: Haversine formula calculates nearest donors (within 50km radius)
- **ML-Powered Ranking**: Intelligent donor scoring based on:
  - Distance from request location
  - Historical response rate
  - Donation history
  - Availability status

### 🗺️ Real-Time Tracking
- Interactive map view with Leaflet.js
- Live donor location updates via WebSocket
- Watch multiple donors simultaneously
- Auto-refresh location markers
- Route visualization (mock/real routing support)

### 🔔 Notifications System
- Real-time push notifications for:
  - New blood requests matching your profile
  - Donor responses to your requests
  - Request status updates
  - System announcements
- Unread notification counter
- In-app notification center
- Mark as read functionality

### 📊 Analytics & Insights
- **Activity Insights**: Donation statistics, response rates, impact metrics
- **Donation History**: Complete log of past donations and requests
- **Blood Demand Forecast**: ML-based prediction of blood group demand
- **Quick Stats**: Real-time dashboard metrics

### 🏥 Hospital Features
- Blood inventory management by group
- Track available units per blood type
- Low stock alerts
- Inventory update logging
- Request history tracking

### 🧬 Health & Eligibility
- Automatic eligibility checks for donors:
  - Age requirements (18-65 years)
  - Weight requirements (minimum 50kg)
  - Time since last donation (90 days minimum)
  - Health status validation
- Profile completeness verification
- Eligibility status display

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLModel ORM
- **Authentication**: JWT (JSON Web Tokens)
- **WebSocket**: Real-time bidirectional communication
- **ML Models**: scikit-learn (RandomForest, GradientBoosting)
- **APIs**: RESTful API design

### Frontend
- **Framework**: React 18 with Vite
- **State Management**: Zustand
- **Routing**: React Router v6
- **Maps**: React-Leaflet with OpenStreetMap
- **HTTP Client**: Axios
- **Styling**: Custom CSS

### Key Libraries
- **Backend**: `fastapi`, `sqlmodel`, `python-jose`, `passlib`, `scikit-learn`, `uvicorn`
- **Frontend**: `react`, `react-router-dom`, `zustand`, `react-leaflet`, `axios`

## 📁 Project Structure

```
BloodBridge/
├── backend/
│   ├── routes/
│   │   ├── auth_routes.py          # Login, register, profile management
│   │   ├── blood_request_routes.py # Blood request CRUD operations
│   │   ├── location_routes.py      # Saved locations management
│   │   ├── hospital_routes.py      # Hospital inventory & features
│   │   └── notification_routes.py  # Notification system
│   ├── models.py                    # Database models (User, Request, Location, etc.)
│   ├── schemas.py                   # Pydantic request/response schemas
│   ├── main.py                      # FastAPI application entry point
│   ├── database.py                  # Database configuration
│   ├── auth.py                      # JWT authentication
│   ├── utils.py                     # Blood compatibility & distance calculations
│   ├── ml_ranker.py                 # ML-based donor ranking
│   ├── ml_training.py               # ML model training & updates
│   ├── websocket_manager.py         # WebSocket connection management
│   ├── eligibility.py               # Health eligibility checks
│   └── requirements.txt             # Python dependencies
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Navbar.jsx           # Main navigation
    │   │   ├── PrivateRoute.jsx     # Protected route wrapper
    │   │   ├── NotificationSidebar.jsx
    │   │   └── DirectionsMap.jsx
    │   ├── pages/
    │   │   ├── Login.jsx            # Authentication
    │   │   ├── Register.jsx
    │   │   ├── DonorDashboard.jsx   # Donor view
    │   │   ├── RequesterDashboard.jsx # Requester view
    │   │   ├── MapView.jsx          # Interactive map
    │   │   ├── ProfileEdit.jsx      # User profile management
    │   │   ├── SavedLocations.jsx   # Location management
    │   │   ├── NotificationsPage.jsx
    │   │   ├── DonationHistoryPage.jsx
    │   │   ├── QuickStatsPage.jsx
    │   │   └── BloodDemandForecast.jsx
    │   ├── services/
    │   │   └── api.js               # API service layer
    │   ├── store/
    │   │   └── authStore.js         # Zustand state management
    │   └── App.jsx                  # Main application component
    └── package.json
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Node.js 16 or higher
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Charan-L574/BloodBridge.git
   cd BloodBridge
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Environment Configuration** (Optional)
   
   Create `backend/.env` file:
   ```env
   DATABASE_URL=sqlite:///./blood_bank.db
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

### Running the Application

**Option 1: Use the start script (Recommended)**
```bash
# Windows
start.bat

# The script will:
# - Activate Python virtual environment
# - Start backend server on http://localhost:8000
# - Start frontend server on http://localhost:3000
```

**Option 2: Manual start**

Terminal 1 - Backend:
```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage Guide

### For Donors

1. **Register** with your details:
   - Full name, email, password
   - Blood group, age, weight
   - Contact information

2. **Add Saved Locations**:
   - Navigate to Profile → Saved Locations
   - Add Home, Office, or custom locations
   - Set your visibility preference

3. **Receive & Respond to Requests**:
   - Get notified when matching requests are created
   - View request details and distance
   - Accept requests and choose tracking mode
   - Track your donation history

### For Requesters

1. **Create Blood Request**:
   - Select blood group needed
   - Set urgency level
   - Add request location (or use saved location)
   - Provide contact details

2. **View Matching Donors**:
   - See donors ranked by ML score
   - View donor locations on map
   - Track live donor movement
   - Contact donors who accepted

3. **Manage Requests**:
   - Update request status
   - Cancel if fulfilled externally
   - View donation history

### For Hospitals

1. **Manage Inventory**:
   - Update blood unit counts by group
   - Track stock levels
   - Get low stock alerts

2. **Create Requests**:
   - Same as requester functionality
   - Access blood demand forecasts
   - View analytics

## 🔑 Key Functionalities

### Blood Group Compatibility
Automatic matching based on medical compatibility:
- **O-**: Universal donor (can donate to all)
- **AB+**: Universal receiver (can receive from all)
- Complete compatibility matrix implemented

### Distance Calculation
- Haversine formula for accurate distance calculation
- Configurable search radius (default: 50km)
- Multi-location matching checks ALL saved donor locations

### ML Donor Ranking
Intelligent scoring algorithm considers:
- **Distance**: Closer donors ranked higher
- **Response Rate**: Historical acceptance rate
- **Donation History**: More donations = higher score
- **Availability**: Active users prioritized

### Real-Time WebSocket Events
- `location_update`: Live GPS coordinates
- `stop_tracking`: End live tracking session
- `watch_request`: Subscribe to donor location updates
- Automatic reconnection handling

### Notification Types
- `blood_request_created`: New matching request
- `donor_responded`: Donor accepted/declined
- `request_fulfilled`: Request completed
- `request_cancelled`: Request cancelled
- `low_stock_alert`: Hospital inventory alerts

## 🔒 Security Features

- Password hashing with bcrypt
- JWT token-based authentication
- Protected API endpoints
- Role-based access control
- SQL injection prevention via SQLModel
- CORS configuration for frontend

## 🧪 Testing

Sample test users are created on first run:
- **Donor**: donor@example.com / password123
- **Requester**: requester@example.com / password123
- **Hospital**: hospital@example.com / password123

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key API endpoints:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /blood-requests/available` - Get matching requests
- `POST /blood-requests` - Create blood request
- `POST /blood-requests/{id}/respond` - Accept/decline request
- `WebSocket /ws/{token}` - Real-time communication


## 👨‍💻 Author

**Charan**
- GitHub: [@Charan-L574](https://github.com/Charan-L574)

## 🙏 Acknowledgments

- OpenStreetMap for map tiles
- FastAPI for the amazing web framework
- React community for excellent libraries

---

**Note**: This is an educational project demonstrating real-time web application development with modern technologies. For production use, additional security measures, testing, and optimizations should be implemented.
