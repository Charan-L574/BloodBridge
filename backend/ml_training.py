"""
ML Model Training and Initialization
This module handles training ML models with real historical data from the database
"""

from sqlmodel import Session, select, func
from models import DonorResponse, BloodRequest, User, DonorResponseStatus
from ml_ranker import response_predictor, ml_ranker
from demand_forecast import demand_model
import numpy as np
from datetime import datetime, timedelta
from typing import Tuple


def train_response_predictor_with_real_data(session: Session) -> Tuple[bool, str]:
    """
    Train donor response prediction model with real historical data
    Returns (success, message)
    """
    print("🔄 Training Response Predictor with real data...")
    
    # Fetch historical donor response data
    statement = (
        select(DonorResponse, BloodRequest, User)
        .join(BloodRequest, DonorResponse.blood_request_id == BloodRequest.id)
        .join(User, DonorResponse.donor_id == User.id)
        .where(DonorResponse.responded_at.isnot(None))
    )
    
    results = session.exec(statement).all()
    
    if len(results) < 50:
        print(f"⚠️ Insufficient data: {len(results)} samples (need 50+). Using synthetic data.")
        return False, f"Insufficient data: {len(results)} samples (need 50+)"
    
    # Prepare training data
    X = []
    y = []
    
    for response, request, donor in results:
        # Calculate distance (simplified - in production, calculate from actual locations)
        distance = 5.0  # Placeholder - would need actual location calculation
        
        # Calculate acceptance rate for this donor
        donor_total = session.exec(
            select(func.count(DonorResponse.id))
            .where(DonorResponse.donor_id == donor.id)
        ).first() or 1
        
        donor_accepted = session.exec(
            select(func.count(DonorResponse.id))
            .where(DonorResponse.donor_id == donor.id)
            .where(DonorResponse.status == DonorResponseStatus.ACCEPTED)
        ).first() or 0
        
        acceptance_rate = donor_accepted / donor_total
        
        # Calculate response time
        response_time = 30.0  # Default
        if response.responded_at and request.created_at:
            time_diff = response.responded_at - request.created_at
            response_time = time_diff.total_seconds() / 60  # minutes
        
        # Features
        has_tracking = 0  # Placeholder - would check donor's visibility settings
        urgency_map = {"low": 0, "medium": 1, "high": 2, "critical": 2}
        urgency = urgency_map.get(request.urgency_level.lower() if request.urgency_level else "medium", 1)
        hour = request.created_at.hour if request.created_at else 12
        
        X.append([distance, acceptance_rate, response_time, has_tracking, urgency, hour])
        y.append(1 if response.status == DonorResponseStatus.ACCEPTED else 0)
    
    # Retrain model
    X_array = np.array(X)
    y_array = np.array(y)
    
    response_predictor.retrain(X_array, y_array)
    
    acceptance_rate = y_array.mean()
    message = f"✅ Response Predictor trained with {len(X)} samples (acceptance rate: {acceptance_rate:.1%})"
    print(message)
    
    return True, message


def train_demand_forecast_with_real_data(session: Session) -> Tuple[bool, str]:
    """
    Train demand forecasting models with real historical data
    Returns (success, message)
    """
    print("🔄 Training Demand Forecast models with real data...")
    
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    
    trained_groups = []
    
    for group in blood_groups:
        # Get historical time series data
        statement = (
            select(
                func.date(BloodRequest.created_at).label('date'),
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
            units = np.array([r[1] or 0 for r in results], dtype=float)
            
            # Train model for this blood group
            if demand_model.train_model(group, dates, units):
                trained_groups.append(group)
                print(f"  ✅ Trained model for {group} with {len(results)} data points")
    
    if trained_groups:
        message = f"✅ Demand Forecast trained for {len(trained_groups)} blood groups: {', '.join(trained_groups)}"
    else:
        message = "⚠️ No sufficient data to train demand forecast models"
    
    print(message)
    return len(trained_groups) > 0, message


def initialize_ml_models(session: Session) -> dict:
    """
    Initialize all ML models - train with real data if available, otherwise use synthetic
    This should be called once when the application starts
    """
    print("=" * 60)
    print("🤖 Initializing ML Models...")
    print("=" * 60)
    
    results = {
        "response_predictor": {"trained_with_real_data": False, "message": ""},
        "demand_forecast": {"trained_with_real_data": False, "message": ""}
    }
    
    # Train Response Predictor
    success, message = train_response_predictor_with_real_data(session)
    results["response_predictor"]["trained_with_real_data"] = success
    results["response_predictor"]["message"] = message
    
    # Train Demand Forecast
    success, message = train_demand_forecast_with_real_data(session)
    results["demand_forecast"]["trained_with_real_data"] = success
    results["demand_forecast"]["message"] = message
    
    # Ranking model uses the response predictor, so it's ready
    results["ranking_model"] = {
        "status": "ready",
        "message": "✅ Ranking model initialized (uses Response Predictor + Gradient Boosting)"
    }
    print(results["ranking_model"]["message"])
    
    print("=" * 60)
    print("🎯 ML Models Initialization Complete")
    print("=" * 60)
    
    return results


def get_training_data_stats(session: Session) -> dict:
    """
    Get statistics about available training data
    """
    # Count donor responses
    total_responses = session.exec(
        select(func.count(DonorResponse.id))
    ).first() or 0
    
    accepted_responses = session.exec(
        select(func.count(DonorResponse.id))
        .where(DonorResponse.status == DonorResponseStatus.ACCEPTED)
    ).first() or 0
    
    # Count blood requests by group
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    requests_by_group = {}
    
    for group in blood_groups:
        count = session.exec(
            select(func.count(BloodRequest.id))
            .where(BloodRequest.blood_group == group)
        ).first() or 0
        requests_by_group[group] = count
    
    # Get date range
    first_request = session.exec(
        select(BloodRequest.created_at)
        .order_by(BloodRequest.created_at)
    ).first()
    
    last_request = session.exec(
        select(BloodRequest.created_at)
        .order_by(BloodRequest.created_at.desc())
    ).first()
    
    return {
        "donor_responses": {
            "total": total_responses,
            "accepted": accepted_responses,
            "acceptance_rate": accepted_responses / total_responses if total_responses > 0 else 0,
            "sufficient_for_training": total_responses >= 50
        },
        "blood_requests": {
            "by_group": requests_by_group,
            "total": sum(requests_by_group.values()),
            "date_range": {
                "first": first_request.isoformat() if first_request else None,
                "last": last_request.isoformat() if last_request else None
            }
        },
        "recommendations": {
            "response_predictor": "Ready for training" if total_responses >= 50 else f"Need {50 - total_responses} more donor responses",
            "demand_forecast": "Ready for training" if sum(requests_by_group.values()) >= 20 else "Need more blood request history"
        }
    }
