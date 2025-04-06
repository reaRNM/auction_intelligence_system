from typing import Dict, List, Optional, Union
import logging
import time
from datetime import datetime
from .scrapers.scraper_factory import ScraperFactory
from .proxy_manager import ProxyManager
from .user_agent_manager import UserAgentManager

logger = logging.getLogger(__name__)

class ScraperService:
    """Service for managing auction scraping operations."""
    
    def __init__(self):
        """Initialize the scraper service."""
        self.scraper_factory = ScraperFactory()
        self.proxy_manager = ProxyManager()
        self.user_agent_manager = UserAgentManager()
        
        # Set managers in factory
        self.scraper_factory.set_proxy_manager(self.proxy_manager)
        self.scraper_factory.set_user_agent_manager(self.user_agent_manager)
    
    def scrape_auction(self, 
                      auction_id: str, 
                      scraper_type: str = "ebay",
                      max_retries: int = 3,
                      retry_delay: int = 5) -> Dict:
        """Scrape an auction by ID.
        
        Args:
            auction_id: Auction ID to scrape
            scraper_type: Type of scraper to use
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary containing auction data
            
        Raises:
            ValueError: If scraping fails after max retries
        """
        scraper = self.scraper_factory.get_scraper(scraper_type)
        
        for attempt in range(max_retries):
            try:
                return scraper.scrape_by_id(auction_id)
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Rotate proxy and user agent on retry
                    self.proxy_manager.rotate_proxy()
                    self.user_agent_manager.rotate_user_agent()
                else:
                    raise ValueError(f"Failed to scrape auction {auction_id} after {max_retries} attempts")
    
    def scrape_auctions(self,
                       auction_ids: List[str],
                       scraper_type: str = "ebay",
                       max_retries: int = 3,
                       retry_delay: int = 5,
                       delay_between: int = 2) -> List[Dict]:
        """Scrape multiple auctions.
        
        Args:
            auction_ids: List of auction IDs to scrape
            scraper_type: Type of scraper to use
            max_retries: Maximum number of retry attempts per auction
            retry_delay: Delay between retries in seconds
            delay_between: Delay between scraping different auctions in seconds
            
        Returns:
            List of dictionaries containing auction data
        """
        results = []
        scraper = self.scraper_factory.get_scraper(scraper_type)
        
        for auction_id in auction_ids:
            try:
                result = self.scrape_auction(
                    auction_id,
                    scraper_type,
                    max_retries,
                    retry_delay
                )
                results.append(result)
                # Add delay between auctions
                time.sleep(delay_between)
            except Exception as e:
                logger.error(f"Failed to scrape auction {auction_id}: {e}")
                results.append({
                    "auction_id": auction_id,
                    "error": str(e),
                    "scraped_at": datetime.utcnow().isoformat()
                })
        
        return results
    
    def scrape_by_url(self,
                     url: str,
                     scraper_type: str = "ebay",
                     max_retries: int = 3,
                     retry_delay: int = 5) -> Dict:
        """Scrape an auction by URL.
        
        Args:
            url: Auction URL to scrape
            scraper_type: Type of scraper to use
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary containing auction data
            
        Raises:
            ValueError: If scraping fails after max retries
        """
        scraper = self.scraper_factory.get_scraper(scraper_type)
        
        for attempt in range(max_retries):
            try:
                return scraper.scrape_by_url(url)
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Rotate proxy and user agent on retry
                    self.proxy_manager.rotate_proxy()
                    self.user_agent_manager.rotate_user_agent()
                else:
                    raise ValueError(f"Failed to scrape URL {url} after {max_retries} attempts")
    
    def scrape_by_urls(self,
                      urls: List[str],
                      scraper_type: str = "ebay",
                      max_retries: int = 3,
                      retry_delay: int = 5,
                      delay_between: int = 2) -> List[Dict]:
        """Scrape multiple auctions by URL.
        
        Args:
            urls: List of auction URLs to scrape
            scraper_type: Type of scraper to use
            max_retries: Maximum number of retry attempts per auction
            retry_delay: Delay between retries in seconds
            delay_between: Delay between scraping different auctions in seconds
            
        Returns:
            List of dictionaries containing auction data
        """
        results = []
        scraper = self.scraper_factory.get_scraper(scraper_type)
        
        for url in urls:
            try:
                result = self.scrape_by_url(
                    url,
                    scraper_type,
                    max_retries,
                    retry_delay
                )
                results.append(result)
                # Add delay between auctions
                time.sleep(delay_between)
            except Exception as e:
                logger.error(f"Failed to scrape URL {url}: {e}")
                results.append({
                    "url": url,
                    "error": str(e),
                    "scraped_at": datetime.utcnow().isoformat()
                })
        
        return results
    
    def get_scraper_stats(self) -> Dict:
        """Get statistics about the scrapers.
        
        Returns:
            Dictionary containing scraper statistics
        """
        stats = {
            "proxy_count": self.proxy_manager.get_proxy_count(),
            "user_agent_count": self.user_agent_manager.get_user_agent_count(),
            "active_scrapers": list(self.scraper_factory.get_all_scrapers().keys())
        }
        return stats 