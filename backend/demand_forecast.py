from datetime import datetime, timedelta
from sqlmodel import Session, select, func
from models import BloodRequest, DonorResponse, RequestStatus
from typing import Dict, List
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import pickle
import os


class DemandForecastModel:
    """
    ML-based demand forecasting using Linear Regression with trend analysis
    Predicts future blood demand based on historical patterns
    """
    
    def __init__(self):
        self.models = {}  # One model per blood group
        self.poly_features = PolynomialFeatures(degree=2)
        self.model_path = "models/demand_forecast.pkl"
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models if exist"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    self.models = pickle.load(f)
            except Exception as e:
                print(f"Could not load demand forecast models: {e}")
    
    def _save_models(self):
        """Save trained models"""
        os.makedirs("models", exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.models, f)
    
    def train_model(self, blood_group: str, dates: np.ndarray, units: np.ndarray):
        """Train model for specific blood group"""
        if len(dates) < 3:
            return False
        
        # Convert dates to days since first date
        days_since_start = (dates - dates[0]).astype('timedelta64[D]').astype(int).reshape(-1, 1)
        
        # Apply polynomial features for non-linear trends
        X_poly = self.poly_features.fit_transform(days_since_start)
        
        # Train linear regression
        model = LinearRegression()
        model.fit(X_poly, units)
        
        self.models[blood_group] = {
            'model': model,
            'start_date': dates[0],
            'last_value': units[-1],
            'mean_value': np.mean(units),
            'std_value': np.std(units)
        }
        
        self._save_models()
        return True
    
    def predict(self, blood_group: str, days_ahead: int, current_date: datetime) -> float:
        """Predict demand for specific blood group"""
        if blood_group not in self.models:
            return 0.0
        
        model_data = self.models[blood_group]
        model = model_data['model']
        start_date = model_data['start_date']
        
        # Calculate days since start
        days_since_start = (np.datetime64(current_date) - start_date).astype('timedelta64[D]').astype(int)
        future_days = days_since_start + days_ahead
        
        # Make prediction
        X_future = self.poly_features.transform([[future_days]])
        prediction = model.predict(X_future)[0]
        
        # Ensure non-negative prediction
        prediction = max(0, prediction)
        
        return prediction


# Global instance
demand_model = DemandForecastModel()


def calculate_demand_forecast(session: Session, days_ahead: int = 7) -> Dict[str, any]:
    """
    Calculate blood demand forecast using ML models
    Returns predictions for each blood group
    """
    # Get historical data from last 60 days for better training
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    
    # Get daily request counts by blood group
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    forecast = {}
    
    for group in blood_groups:
        # Get historical time series data
        statement = (
            select(
                func.date(BloodRequest.created_at).label('date'),
                func.count(BloodRequest.id).label('count'),
                func.sum(BloodRequest.units_needed).label('units')
            )
            .where(BloodRequest.blood_group == group)
            .where(BloodRequest.created_at >= sixty_days_ago)
            .group_by(func.date(BloodRequest.created_at))
            .order_by(func.date(BloodRequest.created_at))
        )
        
        results = session.exec(statement).all()
        
        if len(results) >= 3:
            # Extract dates and units
            dates = np.array([datetime.fromisoformat(str(r[0])) for r in results], dtype='datetime64[D]')
            units = np.array([r[2] or 0 for r in results], dtype=float)
            
            # Train ML model for this blood group
            demand_model.train_model(group, dates, units)
            
            # Make prediction
            predicted_units = demand_model.predict(group, days_ahead, datetime.utcnow())
            
            # Calculate recent trends
            recent_7days = datetime.utcnow() - timedelta(days=7)
            recent_statement = (
                select(func.sum(BloodRequest.units_needed))
                .where(BloodRequest.blood_group == group)
                .where(BloodRequest.created_at >= recent_7days)
            )
            recent_units = session.exec(recent_statement).first() or 0
            
            # Calculate 30-day average
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            thirty_day_statement = (
                select(func.sum(BloodRequest.units_needed))
                .where(BloodRequest.blood_group == group)
                .where(BloodRequest.created_at >= thirty_days_ago)
            )
            thirty_day_units = session.exec(thirty_day_statement).first() or 0
            
            # Determine trend using ML prediction vs historical average
            avg_daily_units = units.mean()
            predicted_daily = predicted_units / days_ahead
            
            if predicted_daily > avg_daily_units * 1.2:
                trend = "increasing"
            elif predicted_daily < avg_daily_units * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
            
            # Calculate urgency score (0-100)
            recent_daily_avg = recent_units / 7
            baseline_daily_avg = thirty_day_units / 30
            
            if baseline_daily_avg > 0:
                urgency_score = min(100, int((recent_daily_avg / baseline_daily_avg) * 50))
            else:
                urgency_score = 0
            
            # Add volatility score based on standard deviation
            volatility = np.std(units) / (avg_daily_units + 1)
            if volatility > 0.5:
                urgency_score += 10
            
            urgency_score = min(100, urgency_score)
            
            # Count recent requests for context
            recent_count_statement = (
                select(func.count(BloodRequest.id))
                .where(BloodRequest.blood_group == group)
                .where(BloodRequest.created_at >= recent_7days)
            )
            recent_request_count = session.exec(recent_count_statement).first() or 0
            
        else:
            # Insufficient data for ML
            predicted_units = 0
            trend = "insufficient_data"
            urgency_score = 0
            recent_request_count = 0
        
        forecast[group] = {
            "predicted_units": round(predicted_units, 1),
            "predicted_requests": round(predicted_units / 1.5, 1),  # Assume avg 1.5 units per request
            "trend": trend,
            "urgency_score": urgency_score,
            "recent_requests_7d": recent_request_count,
            "confidence": "high" if len(results) >= 10 else "medium" if len(results) >= 5 else "low",
            "recommendation": get_recommendation(predicted_units, trend, urgency_score)
        }
    
    # Calculate overall demand
    total_predicted_units = sum(f["predicted_units"] for f in forecast.values())
    
    return {
        "forecast_period_days": days_ahead,
        "generated_at": datetime.utcnow().isoformat(),
        "model_type": "ML-based (Polynomial Regression)",
        "by_blood_group": forecast,
        "total_predicted_units": round(total_predicted_units, 1),
        "high_demand_groups": [
            group for group, data in forecast.items() 
            if data["urgency_score"] >= 60
        ],
        "trends": {
            "increasing": [g for g, d in forecast.items() if d["trend"] == "increasing"],
            "decreasing": [g for g, d in forecast.items() if d["trend"] == "decreasing"],
            "stable": [g for g, d in forecast.items() if d["trend"] == "stable"]
        }
    }


def get_recommendation(predicted_units: float, trend: str, urgency_score: int) -> str:
    """Generate actionable recommendations"""
    if predicted_units == 0:
        return "No demand forecast available. Monitor for new requests."
    
    if urgency_score >= 75:
        return "HIGH PRIORITY: Organize donation drives and contact regular donors immediately."
    elif urgency_score >= 60:
        return "MODERATE PRIORITY: Reach out to donors and ensure adequate inventory."
    elif trend == "increasing":
        return "INCREASING DEMAND: Prepare for higher request volume. Consider donor outreach."
    elif trend == "decreasing":
        return "STABLE: Current inventory levels should be sufficient."
    else:
        return "MONITOR: Track request patterns and maintain standard inventory."


def get_donor_availability_forecast(session: Session) -> Dict[str, int]:
    """
    Get count of available donors by blood group
    """
    from models import User, UserRole
    
    statement = (
        select(
            User.blood_group,
            func.count(User.id).label('count')
        )
        .where(User.role == UserRole.DONOR)
        .where(User.is_available == True)
        .where(User.blood_group.isnot(None))
        .group_by(User.blood_group)
    )
    
    results = session.exec(statement).all()
    
    availability = {}
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    for group in blood_groups:
        group_data = next((r for r in results if r[0] == group), None)
        availability[group] = group_data[1] if group_data else 0
    
    return availability
