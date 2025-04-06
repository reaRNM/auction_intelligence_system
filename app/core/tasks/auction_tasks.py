from celery import shared_task
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.db.config import SessionLocal
from src.models.auction import Auction, AuctionImage, AuctionBid, AuctionStatus
from src.services.scrapers.ebay_scraper import EbayScraper
from src.services.scrapers.local_scraper import LocalScraper

logger = logging.getLogger(__name__)

@shared_task(
    name="src.services.tasks.auction_tasks.update_auction_data",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def update_auction_data(self) -> Dict[str, int]:
    """Update auction data from all sources."""
    try:
        db = SessionLocal()
        scrapers = [
            EbayScraper(),
            LocalScraper(),
        ]
        
        total_updated = 0
        total_new = 0
        
        for scraper in scrapers:
            try:
                # Get active auctions
                active_auctions = db.query(Auction).filter(
                    Auction.status == AuctionStatus.ACTIVE,
                    Auction.source == scraper.source,
                ).all()
                
                # Update existing auctions
                for auction in active_auctions:
                    try:
                        updated_data = scraper.get_auction_data(auction.source_id)
                        if updated_data:
                            auction.update(updated_data)
                            total_updated += 1
                    except Exception as e:
                        logger.error(f"Error updating auction {auction.id}: {e}")
                        continue
                
                # Get new auctions
                new_auctions = scraper.get_new_auctions()
                for auction_data in new_auctions:
                    try:
                        auction = Auction.from_dict(auction_data)
                        db.add(auction)
                        total_new += 1
                    except Exception as e:
                        logger.error(f"Error adding new auction: {e}")
                        continue
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Error with scraper {scraper.__class__.__name__}: {e}")
                continue
        
        return {
            "updated": total_updated,
            "new": total_new,
        }
        
    except Exception as e:
        logger.error(f"Error in update_auction_data: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

@shared_task(
    name="src.services.tasks.auction_tasks.process_auction_images",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def process_auction_images(self, auction_id: int) -> Dict[str, int]:
    """Process and optimize images for an auction."""
    try:
        db = SessionLocal()
        auction = db.query(Auction).get(auction_id)
        
        if not auction:
            raise ValueError(f"Auction {auction_id} not found")
        
        total_processed = 0
        total_optimized = 0
        
        for image in auction.images:
            try:
                # Download and process image
                processed_url = process_image(image.url)
                if processed_url:
                    image.url = processed_url
                    total_processed += 1
                    total_optimized += 1
            except Exception as e:
                logger.error(f"Error processing image {image.id}: {e}")
                continue
        
        db.commit()
        
        return {
            "processed": total_processed,
            "optimized": total_optimized,
        }
        
    except Exception as e:
        logger.error(f"Error in process_auction_images: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

@shared_task(
    name="src.services.tasks.auction_tasks.analyze_auction_trends",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def analyze_auction_trends(self, category: Optional[str] = None) -> Dict[str, float]:
    """Analyze auction trends for a specific category or all categories."""
    try:
        db = SessionLocal()
        
        # Base query
        query = db.query(Auction)
        
        # Filter by category if specified
        if category:
            query = query.filter(Auction.category == category)
        
        # Get auctions from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        query = query.filter(Auction.created_at >= thirty_days_ago)
        
        auctions = query.all()
        
        # Calculate metrics
        total_auctions = len(auctions)
        total_value = sum(a.current_price for a in auctions)
        avg_price = total_value / total_auctions if total_auctions > 0 else 0
        
        # Calculate success rate (auctions that sold)
        sold_auctions = [a for a in auctions if a.status == AuctionStatus.SOLD]
        success_rate = len(sold_auctions) / total_auctions if total_auctions > 0 else 0
        
        # Calculate average time to sale
        sale_times = [
            (a.end_time - a.start_time).total_seconds() / 3600  # Convert to hours
            for a in sold_auctions
        ]
        avg_time_to_sale = sum(sale_times) / len(sale_times) if sale_times else 0
        
        return {
            "total_auctions": total_auctions,
            "total_value": total_value,
            "avg_price": avg_price,
            "success_rate": success_rate,
            "avg_time_to_sale": avg_time_to_sale,
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_auction_trends: {e}")
        raise self.retry(exc=e)
        
    finally:
        db.close()

def process_image(url: str) -> Optional[str]:
    """Process and optimize an image."""
    # TODO: Implement image processing logic
    # This should include:
    # 1. Downloading the image
    # 2. Resizing to appropriate dimensions
    # 3. Optimizing file size
    # 4. Converting to appropriate format
    # 5. Uploading to storage
    # 6. Returning the new URL
    return url 