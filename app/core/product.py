from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class ProductCondition(enum.Enum):
    """Enum for product condition."""
    NEW = "new"
    LIKE_NEW = "like_new"
    VERY_GOOD = "very_good"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    FOR_PARTS = "for_parts"

class Product(Base):
    """Model for product data."""
    
    # Basic product information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[ProductCondition] = mapped_column(
        Enum(ProductCondition),
        nullable=False,
    )
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    sku: Mapped[Optional[str]] = mapped_column(String(100))
    upc: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Product details
    features: Mapped[Optional[dict]] = mapped_column(JSON)
    specifications: Mapped[Optional[dict]] = mapped_column(JSON)
    dimensions: Mapped[Optional[dict]] = mapped_column(JSON)
    weight: Mapped[Optional[float]] = mapped_column(Float)
    
    # Market data
    current_market_price: Mapped[Optional[float]] = mapped_column(Float)
    lowest_market_price: Mapped[Optional[float]] = mapped_column(Float)
    highest_market_price: Mapped[Optional[float]] = mapped_column(Float)
    average_market_price: Mapped[Optional[float]] = mapped_column(Float)
    price_history: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    images: Mapped[List["ProductImage"]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    market_data: Mapped[List["MarketData"]] = relationship(
        "MarketData",
        back_populates="product",
        cascade="all, delete-orphan",
    )

class ProductImage(Base):
    """Model for product images."""
    
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="images")

class MarketData(Base):
    """Model for market data."""
    
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    condition: Mapped[ProductCondition] = mapped_column(
        Enum(ProductCondition),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    url: Mapped[Optional[str]] = mapped_column(String(500))
    seller_rating: Mapped[Optional[float]] = mapped_column(Float)
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="market_data") 