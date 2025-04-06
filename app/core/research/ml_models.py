from typing import Dict, List, Optional, Tuple
import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import xgboost as xgb
import shap
from datetime import datetime
import joblib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PricePredictor:
    """XGBoost model for price prediction."""
    
    def __init__(self):
        """Initialize the price predictor."""
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "brand_encoded",
            "category_encoded",
            "seasonality",
            "gdp_growth",
            "inflation_rate",
            "unemployment_rate"
        ]
        self.model_path = Path(__file__).parent / "models" / "price_predictor.joblib"
        self.scaler_path = Path(__file__).parent / "models" / "price_scaler.joblib"
        
        # Load model if exists
        if self.model_path.exists() and self.scaler_path.exists():
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
    
    def predict(self, features: Dict) -> Tuple[float, Dict]:
        """Predict price and get feature importance.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Tuple of (predicted price, feature importance)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return 0.0, {}
        
        try:
            # Prepare features
            X = self._prepare_features(features)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            
            # Get feature importance
            importance = self._get_feature_importance(X_scaled)
            
            return prediction, importance
            
        except Exception as e:
            logger.error(f"Price prediction failed: {e}")
            return 0.0, {}
    
    def train(self, data: pd.DataFrame) -> None:
        """Train the price prediction model.
        
        Args:
            data: DataFrame containing training data
        """
        try:
            # Prepare features and target
            X = data[self.feature_names]
            y = data["price"]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = xgb.XGBRegressor(
                objective="reg:squarederror",
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6
            )
            self.model.fit(X_scaled, y)
            
            # Save model and scaler
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
    
    def _prepare_features(self, features: Dict) -> np.ndarray:
        """Prepare features for prediction.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Numpy array of prepared features
        """
        # Convert categorical features to numeric
        brand_encoded = hash(features.get("brand", "")) % 1000
        category_encoded = hash(features.get("category", "")) % 1000
        
        # Get economic indicators
        gdp_growth = features.get("gdp_growth", 0.0)
        inflation_rate = features.get("inflation_rate", 0.0)
        unemployment_rate = features.get("unemployment_rate", 0.0)
        
        # Calculate seasonality
        current_month = datetime.now().month
        seasonality = np.sin(2 * np.pi * current_month / 12)
        
        return np.array([[
            brand_encoded,
            category_encoded,
            seasonality,
            gdp_growth,
            inflation_rate,
            unemployment_rate
        ]])
    
    def _get_feature_importance(self, X: np.ndarray) -> Dict:
        """Get feature importance using SHAP values.
        
        Args:
            X: Scaled feature array
            
        Returns:
            Dictionary of feature importance
        """
        try:
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X)
            
            importance = {}
            for i, feature in enumerate(self.feature_names):
                importance[feature] = float(abs(shap_values[0][i]))
            
            return importance
            
        except Exception as e:
            logger.error(f"Feature importance calculation failed: {e}")
            return {}


class ReturnRiskPredictor:
    """Random Forest model for return risk prediction."""
    
    def __init__(self):
        """Initialize the return risk predictor."""
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = [
            "product_type_encoded",
            "condition_encoded",
            "seller_rating",
            "description_length",
            "has_damage_notes",
            "has_returns_accepted"
        ]
        self.model_path = Path(__file__).parent / "models" / "return_risk.joblib"
        self.scaler_path = Path(__file__).parent / "models" / "return_risk_scaler.joblib"
        
        # Load model if exists
        if self.model_path.exists() and self.scaler_path.exists():
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
    
    def predict(self, features: Dict) -> Tuple[str, float]:
        """Predict return risk.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Tuple of (risk category, probability)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return "Unknown", 0.0
        
        try:
            # Prepare features
            X = self._prepare_features(features)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            probability = self.model.predict_proba(X_scaled)[0][1]
            
            # Determine risk category
            if probability > 0.25:
                category = "High"
            elif probability > 0.12:
                category = "Medium"
            else:
                category = "Low"
            
            return category, probability
            
        except Exception as e:
            logger.error(f"Return risk prediction failed: {e}")
            return "Unknown", 0.0
    
    def train(self, data: pd.DataFrame) -> None:
        """Train the return risk prediction model.
        
        Args:
            data: DataFrame containing training data
        """
        try:
            # Prepare features and target
            X = data[self.feature_names]
            y = data["returned"]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=42
            )
            self.model.fit(X_scaled, y)
            
            # Save model and scaler
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
    
    def _prepare_features(self, features: Dict) -> np.ndarray:
        """Prepare features for prediction.
        
        Args:
            features: Dictionary of feature values
            
        Returns:
            Numpy array of prepared features
        """
        # Convert categorical features to numeric
        product_type_encoded = hash(features.get("product_type", "")) % 1000
        condition_encoded = hash(features.get("condition", "")) % 1000
        
        # Get seller rating
        seller_rating = features.get("seller_rating", 0.0)
        
        # Get description features
        description = features.get("description", "")
        description_length = len(description)
        has_damage_notes = 1 if "damage" in description.lower() else 0
        
        # Get returns information
        has_returns_accepted = 1 if features.get("returns_accepted", False) else 0
        
        return np.array([[
            product_type_encoded,
            condition_encoded,
            seller_rating,
            description_length,
            has_damage_notes,
            has_returns_accepted
        ]]) 