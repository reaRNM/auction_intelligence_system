from typing import Dict, List, Optional, Tuple
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from datetime import datetime, timedelta
import joblib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class RiskEngine:
    """Risk engine for shipping damage prediction and cost risk assessment."""
    
    def __init__(self):
        """Initialize the risk engine."""
        self.damage_model = None
        self.damage_scaler = None
        self.model_path = Path(__file__).parent / "models" / "damage_predictor.joblib"
        self.scaler_path = Path(__file__).parent / "models" / "damage_scaler.joblib"
        
        # Load model if exists
        if self.model_path.exists() and self.scaler_path.exists():
            self.damage_model = joblib.load(self.model_path)
            self.damage_scaler = joblib.load(self.scaler_path)
    
    def predict_damage_risk(self, 
                          fragility_score: float,
                          carrier: str,
                          distance: float) -> Tuple[float, Dict]:
        """Predict damage risk for a shipment.
        
        Args:
            fragility_score: Item fragility score (0-10)
            carrier: Shipping carrier name
            distance: Shipping distance in miles
            
        Returns:
            Tuple of (damage probability, feature importance)
        """
        if self.damage_model is None:
            logger.error("Damage prediction model not loaded")
            return 0.0, {}
        
        try:
            # Prepare features
            features = self._prepare_features(fragility_score, carrier, distance)
            
            # Scale features
            features_scaled = self.damage_scaler.transform(features)
            
            # Make prediction
            probability = self.damage_model.predict_proba(features_scaled)[0][1]
            
            # Get feature importance
            importance = self._get_feature_importance(features_scaled)
            
            return probability, importance
            
        except Exception as e:
            logger.error(f"Damage risk prediction failed: {e}")
            return 0.0, {}
    
    def calculate_cost_risk(self, 
                          base_cost: float,
                          distance: float,
                          weight: float,
                          is_holiday: bool = False) -> Dict:
        """Calculate cost risk factors.
        
        Args:
            base_cost: Base shipping cost
            distance: Shipping distance in miles
            weight: Package weight in pounds
            is_holiday: Whether shipping during holiday season
            
        Returns:
            Dictionary containing cost risk factors
        """
        try:
            # Calculate fuel surcharge
            fuel_surcharge = self._calculate_fuel_surcharge(distance, weight)
            
            # Calculate holiday premium
            holiday_premium = self._calculate_holiday_premium(base_cost, is_holiday)
            
            # Calculate total cost risk
            total_cost = base_cost + fuel_surcharge + holiday_premium
            
            return {
                "base_cost": base_cost,
                "fuel_surcharge": fuel_surcharge,
                "holiday_premium": holiday_premium,
                "total_cost": total_cost,
                "risk_factors": {
                    "distance_risk": min(distance / 1000, 1.0),  # Normalize to 0-1
                    "weight_risk": min(weight / 50, 1.0),  # Normalize to 0-1
                    "holiday_risk": 0.2 if is_holiday else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Cost risk calculation failed: {e}")
            return {}
    
    def train_damage_model(self, data: pd.DataFrame) -> None:
        """Train the damage prediction model.
        
        Args:
            data: DataFrame containing training data
        """
        try:
            # Prepare features and target
            X = data[["fragility_score", "carrier_encoded", "distance"]]
            y = data["damaged"]
            
            # Scale features
            self.damage_scaler = StandardScaler()
            X_scaled = self.damage_scaler.fit_transform(X)
            
            # Train model
            self.damage_model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            self.damage_model.fit(X_scaled, y)
            
            # Save model and scaler
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.damage_model, self.model_path)
            joblib.dump(self.damage_scaler, self.scaler_path)
            
        except Exception as e:
            logger.error(f"Damage model training failed: {e}")
    
    def _prepare_features(self, 
                         fragility_score: float,
                         carrier: str,
                         distance: float) -> np.ndarray:
        """Prepare features for damage prediction.
        
        Args:
            fragility_score: Item fragility score
            carrier: Shipping carrier name
            distance: Shipping distance
            
        Returns:
            Numpy array of prepared features
        """
        # Encode carrier
        carrier_encoded = hash(carrier) % 1000
        
        return np.array([[
            fragility_score,
            carrier_encoded,
            distance
        ]])
    
    def _get_feature_importance(self, X: np.ndarray) -> Dict:
        """Get feature importance from model.
        
        Args:
            X: Scaled feature array
            
        Returns:
            Dictionary of feature importance
        """
        try:
            importance = self.damage_model.feature_importances_
            return {
                "fragility_score": float(importance[0]),
                "carrier": float(importance[1]),
                "distance": float(importance[2])
            }
            
        except Exception as e:
            logger.error(f"Feature importance calculation failed: {e}")
            return {}
    
    def _calculate_fuel_surcharge(self, distance: float, weight: float) -> float:
        """Calculate fuel surcharge.
        
        Args:
            distance: Shipping distance in miles
            weight: Package weight in pounds
            
        Returns:
            Fuel surcharge amount
        """
        # Base fuel rate per mile per pound
        base_rate = 0.0001
        
        # Calculate surcharge
        surcharge = base_rate * distance * weight
        
        return round(surcharge, 2)
    
    def _calculate_holiday_premium(self, base_cost: float, is_holiday: bool) -> float:
        """Calculate holiday season premium.
        
        Args:
            base_cost: Base shipping cost
            is_holiday: Whether shipping during holiday season
            
        Returns:
            Holiday premium amount
        """
        if not is_holiday:
            return 0.0
        
        # 20% premium during holiday season
        premium = base_cost * 0.2
        
        return round(premium, 2) 