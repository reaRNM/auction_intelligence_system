from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime
from scipy.optimize import minimize

class OptimizationEngine:
    """Service for optimizing auction and listing parameters using machine learning."""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize the optimization engine.
        
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
        """Train the optimization model.
        
        Args:
            X: Feature matrix of shape (n_samples, n_features).
            y: Target values of shape (n_samples,).
        """
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def optimize(self, data: Dict) -> List[Dict]:
        """Optimize parameters for the given scenario.
        
        Args:
            data: Dictionary containing optimization scenario data.
                Expected format:
                {
                    "current_params": Dict,  # Current parameter values
                    "constraints": Dict,  # Parameter constraints
                    "objective": str,  # Optimization objective
                    "metadata": Dict,  # Optional metadata
                }
        
        Returns:
            List of dictionaries containing optimization results:
            [
                {
                    "parameters": Dict,  # Optimized parameters
                    "objective_value": float,  # Objective function value
                    "confidence": float,  # Optimization confidence score
                    "metadata": Dict,  # Additional metadata
                },
                ...
            ]
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before optimization")
        
        current_params = data["current_params"]
        constraints = data["constraints"]
        objective = data.get("objective", "maximize_revenue")
        metadata = data.get("metadata", {})
        
        # Define objective function
        def objective_function(x):
            # Scale parameters
            x_scaled = self.scaler.transform(x.reshape(1, -1))
            
            # Predict outcome
            prediction = self.model.predict(x_scaled)[0]
            
            # Return negative value for maximization
            return -prediction if objective == "maximize_revenue" else prediction
        
        # Set up parameter bounds
        bounds = []
        for param, value in current_params.items():
            if param in constraints:
                bounds.append((
                    constraints[param].get("min", value * 0.5),
                    constraints[param].get("max", value * 1.5)
                ))
            else:
                bounds.append((value * 0.5, value * 1.5))
        
        # Initial guess
        x0 = np.array([current_params[p] for p in current_params])
        
        # Run optimization
        result = minimize(
            objective_function,
            x0,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 100}
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(result.x)
        
        # Format results
        optimized_params = {
            param: float(value)
            for param, value in zip(current_params.keys(), result.x)
        }
        
        return [{
            "parameters": optimized_params,
            "objective_value": float(-result.fun if objective == "maximize_revenue" else result.fun),
            "confidence": float(confidence),
            "metadata": {
                **metadata,
                "model_version": self.version,
                "optimization_objective": objective,
                "success": result.success,
                "iterations": result.nit,
            }
        }]
    
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
    
    def _calculate_confidence_score(self, parameters: np.ndarray) -> float:
        """Calculate confidence score for optimization results.
        
        Args:
            parameters: Optimized parameter values.
        
        Returns:
            Confidence score between 0 and 1.
        """
        # Scale parameters
        parameters_scaled = self.scaler.transform(parameters.reshape(1, -1))
        
        # Get predictions from all trees
        predictions = np.array([tree.predict(parameters_scaled) for tree in self.model.estimators_])
        
        # Calculate standard deviation of predictions
        std = np.std(predictions)
        
        # Convert to confidence score (inverse of normalized standard deviation)
        max_std = np.max([tree.predict(parameters_scaled).std() for tree in self.model.estimators_])
        if max_std > 0:
            confidence = 1 - (std / max_std)
        else:
            confidence = 1.0
        
        return confidence 