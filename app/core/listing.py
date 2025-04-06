from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Enum, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class ListingStatus(enum.Enum):
    """Enum for listing status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"
    SOLD = "sold"
    CANCELLED = "cancelled"

class ListingPlatform(enum.Enum):
    """Enum for listing platform."""
    EBAY = "ebay"
    AMAZON = "amazon"
    OTHER = "other"

class Listing(Base):
    """Model for listing data."""
    
    # Basic listing information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[ListingPlatform] = mapped_column(
        Enum(ListingPlatform),
        nullable=False,
    )
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus),
        nullable=False,
        default=ListingStatus.DRAFT,
    )
    
    # Item details
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("product.id"),
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Pricing
    price: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_cost: Mapped[Optional[float]] = mapped_column(Float)
    tax_rate: Mapped[Optional[float]] = mapped_column(Float)
    promotion_discount: Mapped[Optional[float]] = mapped_column(Float)
    
    # Listing details
    duration: Mapped[int] = mapped_column(Integer, nullable=False)  # in days
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    auto_relist: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_price_adjust: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # SEO and optimization
    keywords: Mapped[List[str]] = mapped_column(JSON, default=list)
    seo_score: Mapped[Optional[float]] = mapped_column(Float)
    policy_compliance: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Platform-specific data
    platform_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    platform_url: Mapped[Optional[str]] = mapped_column(String(500))
    platform_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    images: Mapped[List["ListingImage"]] = relationship(
        "ListingImage",
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    product: Mapped[Optional["Product"]] = relationship("Product")

class ListingImage(Base):
    """Model for listing images."""
    
    listing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("listing.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    listing: Mapped["Listing"] = relationship("Listing", back_populates="images")

class ListingAnalytics(Base):
    """Model for listing analytics data."""
    
    listing_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("listing.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    views: Mapped[int] = mapped_column(Integer, default=0)
    watchers: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversion_rate: Mapped[Optional[float]] = mapped_column(Float)
    search_rank: Mapped[Optional[int]] = mapped_column(Integer)
    search_terms: Mapped[Optional[List[str]]] = mapped_column(JSON)
    
    # Relationships
    listing: Mapped["Listing"] = relationship("Listing") 