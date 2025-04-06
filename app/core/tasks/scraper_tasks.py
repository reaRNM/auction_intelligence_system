from typing import Dict, List, Optional
import logging
from celery import shared_task
from datetime import datetime
from sqlalchemy.orm import Session
from ..scraper_service import ScraperService
from ..database import get_db
from ..models import Auction, ScrapingLog

logger = logging.getLogger(__name__)

@shared_task
def scrape_auction(auction_id: str, scraper_type: str = "ebay") -> Dict:
    """Celery task to scrape a single auction.
    
    Args:
        auction_id: Auction ID to scrape
        scraper_type: Type of scraper to use
        
    Returns:
        Dictionary containing scraping results
    """
    scraper_service = ScraperService()
    db = next(get_db())
    
    try:
        # Scrape auction
        result = scraper_service.scrape_auction(auction_id, scraper_type)
        
        # Update database
        auction = db.query(Auction).filter(Auction.auction_id == auction_id).first()
        if auction:
            auction.title = result.get("title")
            auction.current_bid = result.get("current_bid")
            auction.brand = result.get("brand")
            auction.model = result.get("model")
            auction.upc = result.get("upc")
            auction.asin = result.get("asin")
            auction.condition = result.get("condition")
            auction.damage_notes = result.get("damage_notes")
            auction.end_time = result.get("end_time")
            auction.seller = result.get("seller")
            auction.shipping = result.get("shipping")
            auction.returns = result.get("returns")
            auction.last_scraped = datetime.utcnow()
            db.commit()
        
        # Log successful scrape
        log = ScrapingLog(
            auction_id=auction_id,
            scraper_type=scraper_type,
            status="success",
            data=result
        )
        db.add(log)
        db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to scrape auction {auction_id}: {e}")
        
        # Log failed scrape
        log = ScrapingLog(
            auction_id=auction_id,
            scraper_type=scraper_type,
            status="error",
            error=str(e)
        )
        db.add(log)
        db.commit()
        
        raise
    
    finally:
        db.close()

@shared_task
def scrape_auctions(auction_ids: List[str], scraper_type: str = "ebay") -> List[Dict]:
    """Celery task to scrape multiple auctions.
    
    Args:
        auction_ids: List of auction IDs to scrape
        scraper_type: Type of scraper to use
        
    Returns:
        List of dictionaries containing scraping results
    """
    scraper_service = ScraperService()
    db = next(get_db())
    
    results = []
    for auction_id in auction_ids:
        try:
            # Scrape auction
            result = scraper_service.scrape_auction(auction_id, scraper_type)
            results.append(result)
            
            # Update database
            auction = db.query(Auction).filter(Auction.auction_id == auction_id).first()
            if auction:
                auction.title = result.get("title")
                auction.current_bid = result.get("current_bid")
                auction.brand = result.get("brand")
                auction.model = result.get("model")
                auction.upc = result.get("upc")
                auction.asin = result.get("asin")
                auction.condition = result.get("condition")
                auction.damage_notes = result.get("damage_notes")
                auction.end_time = result.get("end_time")
                auction.seller = result.get("seller")
                auction.shipping = result.get("shipping")
                auction.returns = result.get("returns")
                auction.last_scraped = datetime.utcnow()
            
            # Log successful scrape
            log = ScrapingLog(
                auction_id=auction_id,
                scraper_type=scraper_type,
                status="success",
                data=result
            )
            db.add(log)
            
        except Exception as e:
            logger.error(f"Failed to scrape auction {auction_id}: {e}")
            
            # Log failed scrape
            log = ScrapingLog(
                auction_id=auction_id,
                scraper_type=scraper_type,
                status="error",
                error=str(e)
            )
            db.add(log)
            
            results.append({
                "auction_id": auction_id,
                "error": str(e),
                "scraped_at": datetime.utcnow().isoformat()
            })
    
    db.commit()
    db.close()
    return results

@shared_task
def scrape_by_url(url: str, scraper_type: str = "ebay") -> Dict:
    """Celery task to scrape an auction by URL.
    
    Args:
        url: Auction URL to scrape
        scraper_type: Type of scraper to use
        
    Returns:
        Dictionary containing scraping results
    """
    scraper_service = ScraperService()
    db = next(get_db())
    
    try:
        # Scrape auction
        result = scraper_service.scrape_by_url(url, scraper_type)
        
        # Extract auction ID from result
        auction_id = result.get("auction_id")
        if auction_id:
            # Update database
            auction = db.query(Auction).filter(Auction.auction_id == auction_id).first()
            if auction:
                auction.title = result.get("title")
                auction.current_bid = result.get("current_bid")
                auction.brand = result.get("brand")
                auction.model = result.get("model")
                auction.upc = result.get("upc")
                auction.asin = result.get("asin")
                auction.condition = result.get("condition")
                auction.damage_notes = result.get("damage_notes")
                auction.end_time = result.get("end_time")
                auction.seller = result.get("seller")
                auction.shipping = result.get("shipping")
                auction.returns = result.get("returns")
                auction.last_scraped = datetime.utcnow()
                db.commit()
        
        # Log successful scrape
        log = ScrapingLog(
            auction_id=auction_id,
            scraper_type=scraper_type,
            status="success",
            data=result
        )
        db.add(log)
        db.commit()
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to scrape URL {url}: {e}")
        
        # Log failed scrape
        log = ScrapingLog(
            url=url,
            scraper_type=scraper_type,
            status="error",
            error=str(e)
        )
        db.add(log)
        db.commit()
        
        raise
    
    finally:
        db.close()

@shared_task
def scrape_by_urls(urls: List[str], scraper_type: str = "ebay") -> List[Dict]:
    """Celery task to scrape multiple auctions by URL.
    
    Args:
        urls: List of auction URLs to scrape
        scraper_type: Type of scraper to use
        
    Returns:
        List of dictionaries containing scraping results
    """
    scraper_service = ScraperService()
    db = next(get_db())
    
    results = []
    for url in urls:
        try:
            # Scrape auction
            result = scraper_service.scrape_by_url(url, scraper_type)
            results.append(result)
            
            # Extract auction ID from result
            auction_id = result.get("auction_id")
            if auction_id:
                # Update database
                auction = db.query(Auction).filter(Auction.auction_id == auction_id).first()
                if auction:
                    auction.title = result.get("title")
                    auction.current_bid = result.get("current_bid")
                    auction.brand = result.get("brand")
                    auction.model = result.get("model")
                    auction.upc = result.get("upc")
                    auction.asin = result.get("asin")
                    auction.condition = result.get("condition")
                    auction.damage_notes = result.get("damage_notes")
                    auction.end_time = result.get("end_time")
                    auction.seller = result.get("seller")
                    auction.shipping = result.get("shipping")
                    auction.returns = result.get("returns")
                    auction.last_scraped = datetime.utcnow()
            
            # Log successful scrape
            log = ScrapingLog(
                auction_id=auction_id,
                url=url,
                scraper_type=scraper_type,
                status="success",
                data=result
            )
            db.add(log)
            
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {e}")
            
            # Log failed scrape
            log = ScrapingLog(
                url=url,
                scraper_type=scraper_type,
                status="error",
                error=str(e)
            )
            db.add(log)
            
            results.append({
                "url": url,
                "error": str(e),
                "scraped_at": datetime.utcnow().isoformat()
            })
    
    db.commit()
    db.close()
    return results 