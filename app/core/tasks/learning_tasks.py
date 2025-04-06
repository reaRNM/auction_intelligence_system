from celery import shared_task
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

from src.db.config import SessionLocal
from src.models.learning import MLModel, TrainingData, ModelPrediction
from src.services.ml.price_predictor import PricePredictor
from src.services.ml.demand_forecaster import DemandForecaster
from src.services.ml.optimization_engine import OptimizationEngine

logger = logging.getLogger(__name__)

@shared_task(
    name="src.services.tasks.learning_tasks.train_models",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def train_models(self) -> Dict[str, any]:
    """Train all machine learning models."""
    try:
        db = SessionLocal()
        
        # Initialize model trainers
        price_predictor = PricePredictor()
        demand_forecaster = DemandForecaster()
        optimization_engine = OptimizationEngine()
        
        results = {
            "price_predictor": train_price_predictor(db, price_predictor),
            "demand_forecaster": train_demand_forecaster(db, demand_forecaster),
            "optimization_engine": train_optimization_engine(db, optimization_engine),
        }
        
        return results
        
    except Exception as e:
        logger.error(f"Error in train_models: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

@shared_task(
    name="src.services.tasks.learning_tasks.generate_predictions",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def generate_predictions(self, model_id: int, data: Dict) -> Dict[str, any]:
    """Generate predictions using a specific model."""
    try:
        db = SessionLocal()
        
        # Get model
        model = db.query(MLModel).filter(MLModel.id == model_id).first()
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # Initialize appropriate model based on type
        if model.type == "price_predictor":
            predictor = PricePredictor()
            predictions = predictor.predict(data)
        elif model.type == "demand_forecaster":
            forecaster = DemandForecaster()
            predictions = forecaster.forecast(data)
        elif model.type == "optimization_engine":
            optimizer = OptimizationEngine()
            predictions = optimizer.optimize(data)
        else:
            raise ValueError(f"Unknown model type: {model.type}")
        
        # Store predictions
        for pred in predictions:
            new_prediction = ModelPrediction(
                model_id=model_id,
                input_data=data,
                prediction=pred["prediction"],
                confidence=pred.get("confidence", 0.0),
                metadata=pred.get("metadata", {}),
            )
            db.add(new_prediction)
        
        db.commit()
        
        return {
            "model_id": model_id,
            "predictions": predictions,
        }
        
    except Exception as e:
        logger.error(f"Error in generate_predictions: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

def train_price_predictor(db: Session, predictor: PricePredictor) -> Dict[str, float]:
    """Train the price prediction model."""
    try:
        # Get training data
        training_data = db.query(TrainingData).filter(
            TrainingData.type == "price",
            TrainingData.timestamp >= datetime.utcnow() - timedelta(days=90)
        ).all()
        
        if not training_data:
            return {"message": "No training data available"}
        
        # Prepare features and target
        X = np.array([d.features for d in training_data])
        y = np.array([d.target for d in training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Train model
        predictor.train(X_train, y_train)
        
        # Evaluate model
        y_pred = predictor.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model
        model = MLModel(
            type="price_predictor",
            version=predictor.version,
            metrics={
                "mse": mse,
                "r2": r2,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
            },
            parameters=predictor.get_parameters(),
        )
        db.add(model)
        db.commit()
        
        return {
            "mse": mse,
            "r2": r2,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }
        
    except Exception as e:
        logger.error(f"Error training price predictor: {e}")
        raise

def train_demand_forecaster(db: Session, forecaster: DemandForecaster) -> Dict[str, float]:
    """Train the demand forecasting model."""
    try:
        # Get training data
        training_data = db.query(TrainingData).filter(
            TrainingData.type == "demand",
            TrainingData.timestamp >= datetime.utcnow() - timedelta(days=180)
        ).all()
        
        if not training_data:
            return {"message": "No training data available"}
        
        # Prepare features and target
        X = np.array([d.features for d in training_data])
        y = np.array([d.target for d in training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Train model
        forecaster.train(X_train, y_train)
        
        # Evaluate model
        y_pred = forecaster.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model
        model = MLModel(
            type="demand_forecaster",
            version=forecaster.version,
            metrics={
                "mse": mse,
                "r2": r2,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
            },
            parameters=forecaster.get_parameters(),
        )
        db.add(model)
        db.commit()
        
        return {
            "mse": mse,
            "r2": r2,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }
        
    except Exception as e:
        logger.error(f"Error training demand forecaster: {e}")
        raise

def train_optimization_engine(db: Session, optimizer: OptimizationEngine) -> Dict[str, float]:
    """Train the optimization engine."""
    try:
        # Get training data
        training_data = db.query(TrainingData).filter(
            TrainingData.type == "optimization",
            TrainingData.timestamp >= datetime.utcnow() - timedelta(days=90)
        ).all()
        
        if not training_data:
            return {"message": "No training data available"}
        
        # Prepare features and target
        X = np.array([d.features for d in training_data])
        y = np.array([d.target for d in training_data])
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        # Train model
        optimizer.train(X_train, y_train)
        
        # Evaluate model
        y_pred = optimizer.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Save model
        model = MLModel(
            type="optimization_engine",
            version=optimizer.version,
            metrics={
                "mse": mse,
                "r2": r2,
                "training_samples": len(X_train),
                "test_samples": len(X_test),
            },
            parameters=optimizer.get_parameters(),
        )
        db.add(model)
        db.commit()
        
        return {
            "mse": mse,
            "r2": r2,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
        }
        
    except Exception as e:
        logger.error(f"Error training optimization engine: {e}")
        raise 