from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta

class DemandForecaster:
    """Service for forecasting product demand using machine learning."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the demand forecaster.
        
        Args:
            model_path: Optional path to load a pre-trained model.
        """
        self.version = "1.0.0"
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the demand forecasting model.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target values of shape (n_samples,).
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def forecast(self, data: Dict) -> List[Dict]:
        """Generate demand forecasts for the given data.
        
        Args:
            data: Dictionary containing feature data for forecasting.
                Expected format:
                {
                    "features": List[List[float]],  # List of feature vectors
                    "horizon": int,  # Number of days to forecast
                    "metadata": Dict,  # Optional metadata about the forecast
                }
        
        Returns:
            List of dictionaries containing forecasts and metadata:
            [
                {
                    "forecast": float,  # Forecasted demand
                    "confidence": float,  # Forecast confidence score
                    "date": str,  # Forecast date (ISO format)
                    "metadata": Dict,  # Additional forecast metadata
                },
                ...
            ]
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before making forecasts")
        
        features = np.array(data["features"])
        horizon = data.get("horizon", 7)  # Default to 7-day forecast
        metadata = data.get("metadata", {})
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Generate base forecast
        base_forecast = self.model.predict(features_scaled)
        
        # Calculate confidence scores
        confidences = self._calculate_confidence_scores(features_scaled)
        
        # Generate time series of forecasts
        results = []
        current_date = datetime.utcnow()
        
        for i in range(horizon):
            forecast_date = current_date + timedelta(days=i)
            
            # Apply time-based adjustments
            adjusted_forecast = self._apply_time_adjustments(
                base_forecast,
                forecast_date,
                metadata.get("seasonality", {})
            )
            
            results.append({
                "forecast": float(adjusted_forecast),
                "confidence": float(confidences),
                "date": forecast_date.isoformat(),
                "metadata": {
                    **metadata,
                    "model_version": self.version,
                    "forecast_day": i + 1,
                }
            })
        
        return results
    
    def save_model(self, path: str) -> None:
        """Save the trained model to disk.
        
        Args:
            path: Path where to save the model.
        """
        if not self.is_trained:
            raise RuntimeError("Cannot save untrained model")
        
        model_data = {
            "model": self.model,
            "scaler": self.scaler,
            "version": self.version,
            "timestamp": datetime.utcnow().isoformat(),
        }
        joblib.dump(model_data, path)
    
    def load_model(self, path: str) -> None:
        """Load a trained model from disk.
        
        Args:
            path: Path to the saved model.
        """
        model_data = joblib.load(path)
        self.model = model_data["model"]
        self.scaler = model_data["scaler"]
        self.version = model_data["version"]
        self.is_trained = True
    
    def get_parameters(self) -> Dict:
        """Get the model's parameters.
        
        Returns:
            Dictionary containing model parameters.
        """
        return {
            "n_estimators": self.model.n_estimators,
            "learning_rate": self.model.learning_rate,
            "max_depth": self.model.max_depth,
            "min_samples_split": self.model.min_samples_split,
            "min_samples_leaf": self.model.min_samples_leaf,
            "random_state": self.model.random_state,
        }
    
    def _calculate_confidence_scores(self, features: np.ndarray) -> np.ndarray:
        """Calculate confidence scores for forecasts.
        
        Args:
            features: Scaled feature matrix.
        
        Returns:
            Array of confidence scores between 0 and 1.
        """
        # Get predictions from all trees
        predictions = np.array([tree.predict(features) for tree in self.model.estimators_])
        
        # Calculate standard deviation of predictions
        std = np.std(predictions, axis=0)
        
        # Convert to confidence scores (inverse of normalized standard deviation)
        max_std = np.max(std)
        if max_std > 0:
            confidence = 1 - (std / max_std)
        else:
            confidence = np.ones_like(std)
        
        return confidence
    
    def _apply_time_adjustments(
        self,
        base_forecast: np.ndarray,
        forecast_date: datetime,
        seasonality: Dict
    ) -> np.ndarray:
        """Apply time-based adjustments to the base forecast.
        
        Args:
            base_forecast: Base demand forecast.
            forecast_date: Date for the forecast.
            seasonality: Dictionary containing seasonality factors.
        
        Returns:
            Adjusted forecast values.
        """
        # Apply day of week adjustment
        dow_factor = seasonality.get("day_of_week", {}).get(str(forecast_date.weekday()), 1.0)
        
        # Apply month adjustment
        month_factor = seasonality.get("month", {}).get(str(forecast_date.month), 1.0)
        
        # Apply holiday adjustment
        holiday_factor = seasonality.get("holidays", {}).get(forecast_date.isoformat(), 1.0)
        
        # Combine all factors
        total_factor = dow_factor * month_factor * holiday_factor
        
        return base_forecast * total_factor 