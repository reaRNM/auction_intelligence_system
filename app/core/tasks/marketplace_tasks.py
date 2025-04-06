from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy.orm import Session

from src.services.marketplace_service import MarketplaceService
from src.db.session import get_db

logger = logging.getLogger(__name__)

@shared_task(
    name="update-marketplace-data",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def update_marketplace_data(self, marketplace_type: str) -> Dict:
    """
    Update marketplace data.
    
    Args:
        marketplace_type: Type of marketplace
        
    Returns:
        Dictionary with update results
    """
    try:
        # Initialize marketplace service
        marketplace_service = MarketplaceService()
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get active listings
            active_listings = db.query(Listing).filter(
                Listing.marketplace_type == marketplace_type,
                Listing.status == "active"
            ).all()
            
            # Update each listing
            updated_count = 0
            for listing in active_listings:
                try:
                    # Get listing details
                    listing_details = marketplace_service.get_listing_details(
                        marketplace_type,
                        listing.marketplace_id
                    )
                    
                    # Update listing
                    marketplace_service.update_listing(
                        marketplace_type,
                        listing.marketplace_id,
                        {
                            "title": listing_details["title"],
                            "description": listing_details["description"],
                            "price": listing_details["price"],
                            "quantity": listing_details["quantity"],
                            "status": listing_details["status"]
                        }
                    )
                    
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update listing {listing.marketplace_id}: {str(e)}")
            
            return {
                "marketplace_type": marketplace_type,
                "updated_count": updated_count,
                "total_listings": len(active_listings)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to update marketplace data: {str(e)}")
        raise self.retry(exc=e)

@shared_task(
    name="update-marketplace-analytics",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def update_marketplace_analytics(self, marketplace_type: str) -> Dict:
    """
    Update marketplace analytics data.
    
    Args:
        marketplace_type: Type of marketplace
        
    Returns:
        Dictionary with update results
    """
    try:
        # Initialize marketplace service
        marketplace_service = MarketplaceService()
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get active listings
            active_listings = db.query(Listing).filter(
                Listing.marketplace_type == marketplace_type,
                Listing.status == "active"
            ).all()
            
            # Update analytics for each listing
            updated_count = 0
            for listing in active_listings:
                try:
                    # Get listing analytics
                    analytics = marketplace_service.get_listing_analytics(
                        marketplace_type,
                        listing.marketplace_id
                    )
                    
                    # Update listing analytics
                    listing.views = analytics["views"]
                    listing.clicks = analytics["clicks"]
                    listing.impressions = analytics["impressions"]
                    listing.conversion_rate = analytics["conversion_rate"]
                    listing.average_position = analytics["average_position"]
                    listing.cost_per_click = analytics["cost_per_click"]
                    listing.total_cost = analytics["total_cost"]
                    listing.revenue = analytics["revenue"]
                    listing.updated_at = datetime.utcnow()
                    
                    db.add(listing)
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update analytics for listing {listing.marketplace_id}: {str(e)}")
            
            # Commit changes
            db.commit()
            
            return {
                "marketplace_type": marketplace_type,
                "updated_count": updated_count,
                "total_listings": len(active_listings)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to update marketplace analytics: {str(e)}")
        raise self.retry(exc=e)

@shared_task(
    name="update-market-data",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def update_market_data(self, category: str, time_range: Optional[str] = None) -> Dict:
    """
    Update market data for a category.
    
    Args:
        category: Category name
        time_range: Optional time range ('7d', '30d', '90d')
        
    Returns:
        Dictionary with update results
    """
    try:
        # Initialize marketplace service
        marketplace_service = MarketplaceService()
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get market data from each marketplace
            marketplace_data = {}
            for marketplace_type in marketplace_service.marketplaces:
                try:
                    marketplace_data[marketplace_type] = marketplace_service.get_market_data(
                        marketplace_type,
                        category,
                        time_range=time_range
                    )
                except Exception as e:
                    logger.error(f"Failed to get market data from {marketplace_type}: {str(e)}")
            
            # Get aggregated market data
            aggregated_data = marketplace_service.get_aggregated_market_data(
                category,
                time_range=time_range
            )
            
            # Update market data in database
            market_data = db.query(MarketData).filter(
                MarketData.category == category
            ).first()
            
            if market_data is None:
                market_data = MarketData(category=category)
                db.add(market_data)
            
            market_data.total_listings = aggregated_data["total_listings"]
            market_data.average_price = aggregated_data["average_price"]
            market_data.min_price = aggregated_data["price_range"]["min"]
            market_data.max_price = aggregated_data["price_range"]["max"]
            market_data.price_trend = aggregated_data["trends"]["overall"]["price_trend"]
            market_data.price_change_percent = aggregated_data["trends"]["overall"]["price_change_percent"]
            market_data.volume_trend = aggregated_data["trends"]["overall"]["volume_trend"]
            market_data.volume_change_percent = aggregated_data["trends"]["overall"]["volume_change_percent"]
            market_data.raw_data = marketplace_data
            market_data.updated_at = datetime.utcnow()
            
            # Commit changes
            db.commit()
            
            return {
                "category": category,
                "total_listings": aggregated_data["total_listings"],
                "average_price": aggregated_data["average_price"],
                "price_range": aggregated_data["price_range"],
                "trends": aggregated_data["trends"]["overall"]
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to update market data: {str(e)}")
        raise self.retry(exc=e)

@shared_task(
    name="optimize-listings",
    bind=True,
    max_retries=3,
    default_retry_delay=300
)
def optimize_listings(self, marketplace_type: str) -> Dict:
    """
    Optimize listings based on market data and analytics.
    
    Args:
        marketplace_type: Type of marketplace
        
    Returns:
        Dictionary with optimization results
    """
    try:
        # Initialize marketplace service
        marketplace_service = MarketplaceService()
        
        # Get database session
        db = next(get_db())
        
        try:
            # Get active listings
            active_listings = db.query(Listing).filter(
                Listing.marketplace_type == marketplace_type,
                Listing.status == "active"
            ).all()
            
            # Optimize each listing
            optimized_count = 0
            for listing in active_listings:
                try:
                    # Get market data
                    market_data = db.query(MarketData).filter(
                        MarketData.category == listing.category
                    ).first()
                    
                    if market_data is None:
                        continue
                    
                    # Calculate optimal price
                    optimal_price = market_data.average_price
                    if market_data.price_trend == "up":
                        optimal_price *= 1.1  # 10% above average
                    elif market_data.price_trend == "down":
                        optimal_price *= 0.9  # 10% below average
                    
                    # Update listing if price difference is significant
                    if abs(listing.price - optimal_price) / listing.price > 0.1:  # 10% difference
                        marketplace_service.update_listing(
                            marketplace_type,
                            listing.marketplace_id,
                            {"price": optimal_price}
                        )
                        optimized_count += 1
                except Exception as e:
                    logger.error(f"Failed to optimize listing {listing.marketplace_id}: {str(e)}")
            
            return {
                "marketplace_type": marketplace_type,
                "optimized_count": optimized_count,
                "total_listings": len(active_listings)
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Failed to optimize listings: {str(e)}")
        raise self.retry(exc=e) 