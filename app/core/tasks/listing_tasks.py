from celery import shared_task
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import os
import json
from dotenv import load_dotenv

from src.db.config import SessionLocal
from src.models.listing import Listing, ListingAnalytics
from src.services.marketplaces.ebay_marketplace import EbayMarketplace
from src.services.marketplaces.amazon_marketplace import AmazonMarketplace
from src.services.marketplaces.local_marketplace import LocalMarketplace
from ..listing.base_generator import BaseGenerator
from ..listing.ebay_generator import EbayGenerator
from ..listing.media_processor import MediaProcessor

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@shared_task(
    name="src.services.tasks.listing_tasks.update_listing_analytics",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def update_listing_analytics(self) -> Dict[str, int]:
    """Update analytics for all active listings."""
    try:
        db = SessionLocal()
        marketplaces = [
            EbayMarketplace(),
            AmazonMarketplace(),
            LocalMarketplace(),
        ]
        
        total_updated = 0
        total_new = 0
        
        # Get all active listings
        listings = db.query(Listing).filter(Listing.status == "active").all()
        
        for listing in listings:
            try:
                for marketplace in marketplaces:
                    try:
                        # Get listing analytics
                        analytics = marketplace.get_listing_analytics(listing.platform_id)
                        
                        if analytics:
                            # Create new analytics entry
                            new_analytics = ListingAnalytics(
                                listing_id=listing.id,
                                views=analytics.get("views", 0),
                                clicks=analytics.get("clicks", 0),
                                impressions=analytics.get("impressions", 0),
                                conversion_rate=analytics.get("conversion_rate", 0.0),
                                average_position=analytics.get("average_position", 0.0),
                                cost_per_click=analytics.get("cost_per_click", 0.0),
                                total_cost=analytics.get("total_cost", 0.0),
                                revenue=analytics.get("revenue", 0.0),
                                raw_data=analytics.get("raw_data"),
                            )
                            
                            db.add(new_analytics)
                            total_new += 1
                            
                            # Update listing analytics
                            update_listing_metrics(db, listing, analytics)
                            
                    except Exception as e:
                        logger.error(f"Error getting analytics from {marketplace.name}: {e}")
                        continue
                
                db.commit()
                total_updated += 1
                
            except Exception as e:
                logger.error(f"Error updating listing {listing.id}: {e}")
                continue
        
        return {
            "updated": total_updated,
            "new_analytics": total_new,
        }
        
    except Exception as e:
        logger.error(f"Error in update_listing_analytics: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

@shared_task(
    name="src.services.tasks.listing_tasks.optimize_listing_performance",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def optimize_listing_performance(self, listing_id: int) -> Dict[str, any]:
    """Optimize listing performance based on analytics data."""
    try:
        db = SessionLocal()
        
        # Get listing and its analytics
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            raise ValueError(f"Listing {listing_id} not found")
        
        analytics = db.query(ListingAnalytics).filter(
            ListingAnalytics.listing_id == listing_id,
            ListingAnalytics.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if not analytics:
            return {"message": "No analytics data available for optimization"}
        
        # Calculate performance metrics
        total_views = sum(a.views for a in analytics)
        total_clicks = sum(a.clicks for a in analytics)
        total_revenue = sum(a.revenue for a in analytics)
        total_cost = sum(a.total_cost for a in analytics)
        
        # Calculate averages
        avg_conversion_rate = sum(a.conversion_rate for a in analytics) / len(analytics)
        avg_position = sum(a.average_position for a in analytics) / len(analytics)
        avg_cpc = sum(a.cost_per_click for a in analytics) / len(analytics)
        
        # Generate optimization suggestions
        suggestions = []
        
        # Check conversion rate
        if avg_conversion_rate < 0.02:  # 2% threshold
            suggestions.append({
                "metric": "conversion_rate",
                "current": avg_conversion_rate,
                "threshold": 0.02,
                "suggestion": "Consider improving product images and description to increase conversion rate"
            })
        
        # Check average position
        if avg_position > 3.0:  # Top 3 threshold
            suggestions.append({
                "metric": "average_position",
                "current": avg_position,
                "threshold": 3.0,
                "suggestion": "Consider adjusting pricing or improving listing quality to improve search position"
            })
        
        # Check cost efficiency
        if total_cost > 0 and (total_revenue / total_cost) < 2.0:  # 2x ROI threshold
            suggestions.append({
                "metric": "roi",
                "current": total_revenue / total_cost,
                "threshold": 2.0,
                "suggestion": "Consider reducing advertising spend or optimizing targeting"
            })
        
        return {
            "listing_id": listing_id,
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "avg_conversion_rate": avg_conversion_rate,
            "avg_position": avg_position,
            "avg_cpc": avg_cpc,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"Error in optimize_listing_performance: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

def update_listing_metrics(db: Session, listing: Listing, analytics: Dict) -> None:
    """Update listing metrics based on new analytics data."""
    # Update current metrics
    listing.current_views = analytics.get("views", 0)
    listing.current_clicks = analytics.get("clicks", 0)
    listing.current_conversion_rate = analytics.get("conversion_rate", 0.0)
    
    # Update historical metrics
    if not listing.historical_metrics:
        listing.historical_metrics = []
    
    listing.historical_metrics.append({
        "timestamp": datetime.utcnow().isoformat(),
        "views": analytics.get("views", 0),
        "clicks": analytics.get("clicks", 0),
        "conversion_rate": analytics.get("conversion_rate", 0.0),
        "revenue": analytics.get("revenue", 0.0),
        "cost": analytics.get("total_cost", 0.0),
    })
    
    # Keep only last 90 days of historical metrics
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    listing.historical_metrics = [
        m for m in listing.historical_metrics
        if datetime.fromisoformat(m["timestamp"]) >= ninety_days_ago
    ]
    
    # Update aggregate metrics
    if listing.historical_metrics:
        total_views = sum(m["views"] for m in listing.historical_metrics)
        total_clicks = sum(m["clicks"] for m in listing.historical_metrics)
        total_revenue = sum(m["revenue"] for m in listing.historical_metrics)
        total_cost = sum(m["cost"] for m in listing.historical_metrics)
        
        listing.total_views = total_views
        listing.total_clicks = total_clicks
        listing.total_revenue = total_revenue
        listing.total_cost = total_cost
        listing.roi = (total_revenue - total_cost) / total_cost if total_cost > 0 else 0.0

@shared_task(name="generate-listing")
def generate_listing(product_data: Dict,
                    media_files: List[str],
                    strategy: Dict) -> Dict:
    """Generate a complete listing.
    
    Args:
        product_data: Product information dictionary
        media_files: List of media file paths
        strategy: Listing strategy dictionary
        
    Returns:
        Generated listing dictionary
    """
    try:
        logger.info(f"Generating listing for product: {product_data.get('title', 'Unknown')}")
        
        # Initialize services
        media_processor = MediaProcessor()
        generator = EbayGenerator()
        
        # Process media files
        processed_images = media_processor.process_images(
            media_files,
            strategy.get("media_options", {})
        )
        
        # Generate video if requested
        video_file = ""
        if strategy.get("generate_video", False):
            video_file = media_processor.generate_video(
                processed_images,
                strategy.get("video_options", {})
            )
        
        # Generate listing
        listing = generator.generate_listing(
            product_data,
            processed_images + ([video_file] if video_file else []),
            strategy
        )
        
        # Log generation
        _log_listing_generation(listing)
        
        return listing
        
    except Exception as e:
        logger.error(f"Listing generation failed: {e}")
        return {}

@shared_task(name="process-media")
def process_media(media_files: List[str],
                 options: Dict) -> Dict:
    """Process media files for listings.
    
    Args:
        media_files: List of media file paths
        options: Processing options dictionary
        
    Returns:
        Dictionary with processed file paths
    """
    try:
        logger.info(f"Processing {len(media_files)} media files")
        
        # Initialize media processor
        processor = MediaProcessor()
        
        # Process images
        processed_images = processor.process_images(media_files, options)
        
        # Generate video if requested
        video_file = ""
        if options.get("generate_video", False):
            video_file = processor.generate_video(processed_images, options)
        
        return {
            "processed_images": processed_images,
            "video_file": video_file
        }
        
    except Exception as e:
        logger.error(f"Media processing failed: {e}")
        return {
            "processed_images": media_files,
            "video_file": ""
        }

@shared_task(name="optimize-listing")
def optimize_listing(listing: Dict,
                    optimization_data: Dict) -> Dict:
    """Optimize an existing listing.
    
    Args:
        listing: Current listing dictionary
        optimization_data: Optimization parameters
        
    Returns:
        Optimized listing dictionary
    """
    try:
        logger.info(f"Optimizing listing: {listing.get('title', 'Unknown')}")
        
        # Initialize generator
        generator = EbayGenerator()
        
        # Extract keywords
        keywords = generator._get_keywords(listing)
        
        # Optimize title
        optimized_title = generator.optimize_title(
            listing,
            keywords,
            optimization_data.get("title_options", {})
        )
        
        # Generate description
        description = generator.generate_description(
            listing,
            optimization_data.get("description_options", {})
        )
        
        # Calculate price
        price = generator.calculate_price(
            listing,
            optimization_data.get("pricing_options", {})
        )
        
        # Update listing
        listing.update({
            "title": optimized_title,
            "description": description,
            "price": price
        })
        
        # Log optimization
        _log_listing_optimization(listing)
        
        return listing
        
    except Exception as e:
        logger.error(f"Listing optimization failed: {e}")
        return listing

def _log_listing_generation(listing: Dict):
    """Log listing generation details.
    
    Args:
        listing: Generated listing dictionary
    """
    try:
        log_file = os.path.join(
            os.getenv("LOGS_DIR", "logs"),
            "listing_generation.log"
        )
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "listing_id": listing.get("id", ""),
            "title": listing.get("title", ""),
            "media_count": len(listing.get("media_assets", [])),
            "optimization_metrics": listing.get("optimization_metrics", {})
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    except Exception as e:
        logger.error(f"Listing generation logging failed: {e}")

def _log_listing_optimization(listing: Dict):
    """Log listing optimization details.
    
    Args:
        listing: Optimized listing dictionary
    """
    try:
        log_file = os.path.join(
            os.getenv("LOGS_DIR", "logs"),
            "listing_optimization.log"
        )
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "listing_id": listing.get("id", ""),
            "title": listing.get("title", ""),
            "price": listing.get("price", {}),
            "optimization_metrics": listing.get("optimization_metrics", {})
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
            
    except Exception as e:
        logger.error(f"Listing optimization logging failed: {e}") 