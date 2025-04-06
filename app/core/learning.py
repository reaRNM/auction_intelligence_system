from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class ModelType(enum.Enum):
    """Enum for model types."""
    PRICE_PREDICTION = "price_prediction"
    PROFIT_ANALYSIS = "profit_analysis"
    LISTING_OPTIMIZATION = "listing_optimization"
    SEARCH_RANKING = "search_ranking"

class ModelStatus(enum.Enum):
    """Enum for model status."""
    TRAINING = "training"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    FAILED = "failed"

class MLModel(Base):
    """Model for machine learning models."""
    
    # Basic model information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[ModelType] = mapped_column(
        Enum(ModelType),
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus),
        nullable=False,
        default=ModelStatus.TRAINING,
    )
    
    # Model details
    description: Mapped[Optional[str]] = mapped_column(Text)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    features: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    hyperparameters: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Performance metrics
    accuracy: Mapped[Optional[float]] = mapped_column(Float)
    precision: Mapped[Optional[float]] = mapped_column(Float)
    recall: Mapped[Optional[float]] = mapped_column(Float)
    f1_score: Mapped[Optional[float]] = mapped_column(Float)
    mse: Mapped[Optional[float]] = mapped_column(Float)
    mae: Mapped[Optional[float]] = mapped_column(Float)
    
    # Training information
    training_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    training_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    training_samples: Mapped[Optional[int]] = mapped_column(Integer)
    validation_samples: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Model storage
    model_path: Mapped[str] = mapped_column(String(500), nullable=False)
    scaler_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Relationships
    training_data: Mapped[List["TrainingData"]] = relationship(
        "TrainingData",
        back_populates="model",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[List["ModelPrediction"]] = relationship(
        "ModelPrediction",
        back_populates="model",
        cascade="all, delete-orphan",
    )

class TrainingData(Base):
    """Model for training data."""
    
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("mlmodel.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    target: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[Optional[float]] = mapped_column(Float, default=1.0)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="training_data")

class ModelPrediction(Base):
    """Model for model predictions."""
    
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("mlmodel.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    prediction: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    actual_value: Mapped[Optional[float]] = mapped_column(Float)
    error: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relationships
    model: Mapped["MLModel"] = relationship("MLModel", back_populates="predictions") 