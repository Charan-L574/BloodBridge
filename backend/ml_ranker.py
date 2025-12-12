import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import os


class DonorResponsePredictor:
    """
    ML Model to predict donor acceptance probability using Random Forest
    Features: distance, past_acceptance_rate, response_time, availability, urgency, time_of_day
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            min_samples_split=5
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "models/donor_response_predictor.pkl"
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.is_trained = True
            except Exception as e:
                print(f"Could not load model: {e}")
                self._train_with_synthetic_data()
        else:
            self._train_with_synthetic_data()
    
    def _save_model(self):
        """Save trained model"""
        os.makedirs("models", exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
    
    def _train_with_synthetic_data(self):
        """Train model with synthetic data to bootstrap"""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate synthetic training data
        X = np.random.rand(n_samples, 6)
        X[:, 0] = X[:, 0] * 20  # distance: 0-20 km
        X[:, 1] = X[:, 1]  # past_acceptance_rate: 0-1
        X[:, 2] = X[:, 2] * 120  # avg_response_time: 0-120 minutes
        X[:, 3] = np.random.choice([0, 1], n_samples)  # has_live_tracking
        X[:, 4] = np.random.choice([0, 1, 2], n_samples)  # urgency: 0=low, 1=medium, 2=high
        X[:, 5] = np.random.randint(0, 24, n_samples)  # hour_of_day
        
        # Generate labels based on realistic patterns
        # Higher acceptance for: close distance, high past rate, fast response, urgent cases
        y = np.zeros(n_samples, dtype=int)
        for i in range(n_samples):
            score = (
                (20 - X[i, 0]) / 20 * 0.3 +  # distance
                X[i, 1] * 0.4 +  # past acceptance
                (120 - X[i, 2]) / 120 * 0.2 +  # response time
                X[i, 3] * 0.1  # live tracking
            )
            # Add urgency boost
            if X[i, 4] == 2:  # high urgency
                score += 0.15
            # Add time of day effect (better during day hours)
            if 8 <= X[i, 5] <= 20:
                score += 0.1
            
            y[i] = 1 if score + np.random.normal(0, 0.15) > 0.5 else 0
        
        # Train model
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self._save_model()
    
    def predict_acceptance_probability(
        self,
        distance_km: float,
        past_acceptance_rate: float = 0.5,
        avg_response_time_minutes: float = 30.0,
        has_live_tracking: bool = False,
        urgency_level: int = 1,  # 0=low, 1=medium, 2=high
        hour_of_day: Optional[int] = None
    ) -> float:
        """Predict probability of donor accepting (0-1)"""
        if hour_of_day is None:
            hour_of_day = datetime.now().hour
        
        features = np.array([[
            distance_km,
            past_acceptance_rate,
            avg_response_time_minutes,
            1 if has_live_tracking else 0,
            urgency_level,
            hour_of_day
        ]])
        
        features_scaled = self.scaler.transform(features)
        probability = self.model.predict_proba(features_scaled)[0][1]
        return round(probability, 3)
    
    def retrain(self, X: np.ndarray, y: np.ndarray):
        """Retrain model with new data"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self._save_model()


class DonorRankingModel:
    """
    ML Model to rank donors by predicted response speed using Gradient Boosting
    Features: distance, acceptance_probability, past_response_time, availability, urgency
    """
    
    def __init__(self):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "models/donor_ranking_model.pkl"
        self.predictor = DonorResponsePredictor()
        self._load_model()
    
    def _load_model(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.is_trained = True
            except Exception as e:
                print(f"Could not load ranking model: {e}")
                self._train_with_synthetic_data()
        else:
            self._train_with_synthetic_data()
    
    def _save_model(self):
        """Save trained model"""
        os.makedirs("models", exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
    
    def _train_with_synthetic_data(self):
        """Train model with synthetic data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Generate synthetic training data
        X = np.random.rand(n_samples, 5)
        X[:, 0] = X[:, 0] * 20  # distance
        X[:, 1] = X[:, 1]  # acceptance_probability
        X[:, 2] = X[:, 2] * 120  # past_response_time
        X[:, 3] = np.random.choice([0, 1], n_samples)  # has_live_tracking
        X[:, 4] = np.random.choice([0, 1, 2], n_samples)  # urgency
        
        # Target: predicted response time in minutes
        y = np.zeros(n_samples)
        for i in range(n_samples):
            base_time = 30  # base 30 minutes
            # Adjust based on features
            time_adjustment = (
                X[i, 0] * 2 +  # distance adds time
                (1 - X[i, 1]) * 20 +  # low acceptance probability = slower
                X[i, 2] * 0.5 -  # past response time pattern
                X[i, 3] * 10 -  # live tracking reduces time
                X[i, 4] * 5  # urgency reduces time
            )
            y[i] = max(5, base_time + time_adjustment + np.random.normal(0, 5))
        
        # Train model to predict response time
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self._save_model()
    
    def predict_response_time(
        self,
        distance_km: float,
        acceptance_probability: float,
        avg_response_time_minutes: float = 30.0,
        has_live_tracking: bool = False,
        urgency_level: int = 1
    ) -> float:
        """Predict expected response time in minutes"""
        features = np.array([[
            distance_km,
            acceptance_probability,
            avg_response_time_minutes,
            1 if has_live_tracking else 0,
            urgency_level
        ]])
        
        features_scaled = self.scaler.transform(features)
        response_time = self.model.predict(features_scaled)[0]
        return max(5.0, round(response_time, 1))
    
    def calculate_score(
        self,
        distance_km: float,
        past_acceptance_rate: float = 0.5,
        avg_response_time_minutes: float = 30.0,
        has_live_tracking: bool = False,
        urgency_level: int = 1
    ) -> float:
        """Calculate ML-based ranking score (0-100, higher is better)"""
        # Get acceptance probability from predictor model
        acceptance_prob = self.predictor.predict_acceptance_probability(
            distance_km, past_acceptance_rate, avg_response_time_minutes,
            has_live_tracking, urgency_level
        )
        
        # Get predicted response time from ranking model
        predicted_response_time = self.predict_response_time(
            distance_km, acceptance_prob, avg_response_time_minutes,
            has_live_tracking, urgency_level
        )
        
        # Calculate composite score
        # Higher acceptance probability = higher score
        # Lower response time = higher score
        acceptance_score = acceptance_prob * 60
        response_score = max(0, 40 - (predicted_response_time / 3))
        
        final_score = acceptance_score + response_score
        return round(min(100, max(0, final_score)), 2)
    
    def rank_donors(self, donor_data: List[Dict]) -> List[Dict]:
        """Rank donors using ML models"""
        for donor in donor_data:
            distance = donor.get('distance_km', 5.0)
            past_rate = donor.get('past_acceptance_rate', 0.5)
            response_time = donor.get('avg_response_time_minutes', 30.0)
            has_tracking = donor.get('has_live_tracking', False)
            urgency = donor.get('urgency_level', 1)
            
            # Calculate ML score
            ml_score = self.calculate_score(
                distance, past_rate, response_time, has_tracking, urgency
            )
            
            # Calculate acceptance probability
            acceptance_prob = self.predictor.predict_acceptance_probability(
                distance, past_rate, response_time, has_tracking, urgency
            )
            
            # Calculate predicted response time
            predicted_response = self.predict_response_time(
                distance, acceptance_prob, response_time, has_tracking, urgency
            )
            
            donor['ml_score'] = ml_score
            donor['acceptance_probability'] = acceptance_prob
            donor['predicted_response_minutes'] = predicted_response
        
        # Sort by ML score (descending)
        ranked_donors = sorted(donor_data, key=lambda x: x['ml_score'], reverse=True)
        return ranked_donors
    
    def retrain(self, X: np.ndarray, y: np.ndarray):
        """Retrain model with new data"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True
        self._save_model()


# Global instances
ml_ranker = DonorRankingModel()
response_predictor = DonorResponsePredictor()
