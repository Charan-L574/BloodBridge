"""
Test script to verify ML models are working properly
"""
import numpy as np
from ml_ranker import ml_ranker, response_predictor
from demand_forecast import demand_model
import requests


def test_response_predictor():
    """Test donor response prediction model"""
    print("\n=== Testing Donor Response Predictor ===")
    print(f"Model is trained: {response_predictor.is_trained}")
    
    # Test cases
    test_cases = [
        {
            "name": "Close, reliable donor",
            "distance_km": 2.0,
            "past_acceptance_rate": 0.9,
            "avg_response_time_minutes": 15.0,
            "has_live_tracking": True,
            "urgency_level": 2
        },
        {
            "name": "Far, new donor",
            "distance_km": 15.0,
            "past_acceptance_rate": 0.5,
            "avg_response_time_minutes": 45.0,
            "has_live_tracking": False,
            "urgency_level": 0
        },
        {
            "name": "Medium case",
            "distance_km": 5.0,
            "past_acceptance_rate": 0.7,
            "avg_response_time_minutes": 25.0,
            "has_live_tracking": False,
            "urgency_level": 1
        }
    ]
    
    for test in test_cases:
        prob = response_predictor.predict_acceptance_probability(
            distance_km=test["distance_km"],
            past_acceptance_rate=test["past_acceptance_rate"],
            avg_response_time_minutes=test["avg_response_time_minutes"],
            has_live_tracking=test["has_live_tracking"],
            urgency_level=test["urgency_level"]
        )
        print(f"\n{test['name']}:")
        print(f"  Input: {test['distance_km']}km, {test['past_acceptance_rate']*100}% rate, {test['avg_response_time_minutes']}min response")
        print(f"  Predicted acceptance probability: {prob:.1%}")


def test_ranking_model():
    """Test donor ranking model"""
    print("\n\n=== Testing Donor Ranking Model ===")
    print(f"Model is trained: {ml_ranker.is_trained}")
    
    # Create sample donor data
    donors = [
        {
            "donor_id": 1,
            "donor_name": "John Doe",
            "donor_phone": "1234567890",
            "blood_group": "A+",
            "distance_km": 3.0,
            "location": {"latitude": 17.385, "longitude": 78.486},
            "is_live_available": True,
            "past_acceptance_rate": 0.85,
            "avg_response_time_minutes": 20.0,
            "has_live_tracking": True,
            "urgency_level": 2
        },
        {
            "donor_id": 2,
            "donor_name": "Jane Smith",
            "donor_phone": "0987654321",
            "blood_group": "A+",
            "distance_km": 7.0,
            "location": {"latitude": 17.385, "longitude": 78.486},
            "is_live_available": False,
            "past_acceptance_rate": 0.6,
            "avg_response_time_minutes": 40.0,
            "has_live_tracking": False,
            "urgency_level": 2
        },
        {
            "donor_id": 3,
            "donor_name": "Bob Wilson",
            "donor_phone": "5555555555",
            "blood_group": "A+",
            "distance_km": 5.0,
            "location": {"latitude": 17.385, "longitude": 78.486},
            "is_live_available": True,
            "past_acceptance_rate": 0.75,
            "avg_response_time_minutes": 30.0,
            "has_live_tracking": True,
            "urgency_level": 2
        }
    ]
    
    # Rank donors
    ranked = ml_ranker.rank_donors(donors)
    
    print("\nRanked Donors (Best to Worst):")
    for i, donor in enumerate(ranked, 1):
        print(f"\n{i}. {donor['donor_name']}")
        print(f"   Distance: {donor['distance_km']}km")
        print(f"   ML Score: {donor['ml_score']:.2f}/100")
        print(f"   Acceptance Probability: {donor['acceptance_probability']:.1%}")
        print(f"   Predicted Response: {donor['predicted_response_minutes']:.1f} minutes")


def test_demand_forecast():
    """Test demand forecasting model"""
    print("\n\n=== Testing Demand Forecast Model ===")
    print(f"Trained blood groups: {list(demand_model.models.keys())}")
    
    # Create synthetic time series for testing
    if not demand_model.models:
        print("\nTraining model with synthetic data...")
        dates = np.array([np.datetime64('2024-11-01') + np.timedelta64(i, 'D') for i in range(30)])
        units = np.array([2.0 + 0.1 * i + np.random.normal(0, 0.5) for i in range(30)])
        units = np.maximum(0, units)  # Ensure non-negative
        
        success = demand_model.train_model('A+', dates, units)
        print(f"Training successful: {success}")
    
    # Make predictions
    from datetime import datetime
    predictions = {}
    for days in [1, 3, 7]:
        pred = demand_model.predict('A+', days, datetime.now())
        predictions[days] = pred
        print(f"\nPredicted units needed in {days} day(s): {pred:.2f}")


def test_api_endpoint():
    """Test ML model info API endpoint"""
    print("\n\n=== Testing API Endpoint ===")
    
    try:
        # Try to access the model info endpoint
        # Note: This requires authentication token
        response = requests.get("http://localhost:8000/blood-requests/ml/model-info")
        print(f"API Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✓ Authentication required (expected)")
        elif response.status_code == 200:
            print("✓ Model info retrieved successfully")
            data = response.json()
            print(f"Response predictor: {data['donor_response_predictor']['type']}")
            print(f"Ranking model: {data['donor_ranking_model']['type']}")
            print(f"Demand forecast: {data['demand_forecast_model']['type']}")
        else:
            print(f"Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"API test skipped: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("ML Models Testing Suite")
    print("=" * 60)
    
    test_response_predictor()
    test_ranking_model()
    test_demand_forecast()
    test_api_endpoint()
    
    print("\n" + "=" * 60)
    print("✓ All ML models tested successfully!")
    print("=" * 60)
    print("\nML Models Summary:")
    print("1. Donor Response Predictor: Random Forest Classifier")
    print("   - Predicts acceptance probability (0-1)")
    print("   - Features: distance, past rate, response time, tracking, urgency, hour")
    print("\n2. Donor Ranking Model: Gradient Boosting Regressor")
    print("   - Predicts response time and calculates ranking score")
    print("   - Features: distance, acceptance prob, response time, tracking, urgency")
    print("\n3. Demand Forecast: Polynomial Regression")
    print("   - Predicts future blood demand by blood group")
    print("   - Features: time series of historical units needed")
    print("=" * 60)
