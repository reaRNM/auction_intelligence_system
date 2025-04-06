from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base

class AuctionStatus(enum.Enum):
    """Enum for auction status."""
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"
    SOLD = "sold"

class AuctionSource(enum.Enum):
    """Enum for auction source."""
    EBAY = "ebay"
    LOCAL = "local"
    OTHER = "other"

class Auction(Base):
    """Model for auction data."""
    
    # Basic auction information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    source: Mapped[AuctionSource] = mapped_column(
        Enum(AuctionSource),
        nullable=False,
    )
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Auction details
    status: Mapped[AuctionStatus] = mapped_column(
        Enum(AuctionStatus),
        nullable=False,
        default=AuctionStatus.ACTIVE,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    starting_price: Mapped[float] = mapped_column(Float, nullable=False)
    buy_now_price: Mapped[Optional[float]] = mapped_column(Float)
    
    # Item details
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Additional metadata
    location: Mapped[Optional[str]] = mapped_column(String(200))
    seller_rating: Mapped[Optional[float]] = mapped_column(Float)
    num_bids: Mapped[int] = mapped_column(Integer, default=0)
    shipping_info: Mapped[Optional[dict]] = mapped_column(JSON)
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Relationships
    images: Mapped[List["AuctionImage"]] = relationship(
        "AuctionImage",
        back_populates="auction",
        cascade="all, delete-orphan",
    )
    bids: Mapped[List["AuctionBid"]] = relationship(
        "AuctionBid",
        back_populates="auction",
        cascade="all, delete-orphan",
    )

class AuctionImage(Base):
    """Model for auction images."""
    
    auction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auction.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_primary: Mapped[bool] = mapped_column(default=False)
    
    # Relationships
    auction: Mapped["Auction"] = relationship("Auction", back_populates="images")

class AuctionBid(Base):
    """Model for auction bids."""
    
    auction_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("auction.id", ondelete="CASCADE"),
        nullable=False,
    )
    bidder_id: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    bid_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    
    # Relationships
    auction: Mapped["Auction"] = relationship("Auction", back_populates="bids") 