from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

class PricePredictor:
    """Service for predicting product prices using machine learning."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the price predictor.
        
        Args:
            model_path: Optional path to load a pre-trained model.
        """
        self.version = "1.0.0"
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the price prediction model.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target values of shape (n_samples,).
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def predict(self, data: Dict) -> List[Dict]:
        """Generate price predictions for the given data.
        
        Args:
            data: Dictionary containing feature data for prediction.
                Expected format:
                {
                    "features": List[List[float]],  # List of feature vectors
                    "metadata": Dict,  # Optional metadata about the prediction
                }
        
        Returns:
            List of dictionaries containing predictions and metadata:
            [
                {
                    "prediction": float,  # Predicted price
                    "confidence": float,  # Prediction confidence score
                    "metadata": Dict,  # Additional prediction metadata
                },
                ...
            ]
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before making predictions")
        
        features = np.array(data["features"])
        metadata = data.get("metadata", {})
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Generate predictions
        predictions = self.model.predict(features_scaled)
        
        # Calculate confidence scores using prediction variance
        confidences = self._calculate_confidence_scores(features_scaled)
        
        # Format results
        results = []
        for pred, conf in zip(predictions, confidences):
            results.append({
                "prediction": float(pred),
                "confidence": float(conf),
                "metadata": {
                    **metadata,
                    "timestamp": datetime.utcnow().isoformat(),
                    "model_version": self.version,
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
            "max_depth": self.model.max_depth,
            "min_samples_split": self.model.min_samples_split,
            "min_samples_leaf": self.model.min_samples_leaf,
            "random_state": self.model.random_state,
        }
    
    def _calculate_confidence_scores(self, features: np.ndarray) -> np.ndarray:
        """Calculate confidence scores for predictions.
        
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