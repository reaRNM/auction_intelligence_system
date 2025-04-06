from typing import Dict, Optional
import logging
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from .base_scraper import BaseScraper
from ..proxy_manager import ProxyManager
from ..user_agent_manager import UserAgentManager

logger = logging.getLogger(__name__)

class EbayScraper(BaseScraper):
    """eBay auction scraper implementation."""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None, 
                 user_agent_manager: Optional[UserAgentManager] = None):
        """Initialize the eBay scraper.
        
        Args:
            proxy_manager: Optional proxy manager instance
            user_agent_manager: Optional user agent manager instance
        """
        super().__init__(proxy_manager, user_agent_manager)
        self.base_url = "https://www.ebay.com"
    
    def scrape_by_id(self, auction_id: str) -> Dict:
        """Scrape an eBay auction by ID.
        
        Args:
            auction_id: eBay auction ID
            
        Returns:
            Dictionary containing auction data
        """
        url = f"{self.base_url}/itm/{auction_id}"
        return self.scrape_by_url(url)
    
    def scrape_by_url(self, url: str) -> Dict:
        """Scrape an eBay auction by URL.
        
        Args:
            url: eBay auction URL
            
        Returns:
            Dictionary containing auction data
        """
        # Get proxy and user agent
        proxy = self.proxy_manager.get_proxy() if self.proxy_manager else None
        user_agent = self.user_agent_manager.get_user_agent() if self.user_agent_manager else None
        
        # Set up headers
        headers = {
            "User-Agent": user_agent or "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        
        try:
            # Make request
            response = requests.get(
                url,
                headers=headers,
                proxies=proxy,
                timeout=30
            )
            response.raise_for_status()
            
            # Check for CAPTCHA
            if self._handle_captcha(response.text):
                logger.warning("CAPTCHA detected, rotating proxy and user agent")
                if self.proxy_manager:
                    self.proxy_manager.rotate_proxy()
                if self.user_agent_manager:
                    self.user_agent_manager.rotate_user_agent()
                return self.scrape_by_url(url)
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract data
            data = {
                "auction_id": self._extract_lot_number(soup),
                "title": self._extract_title(soup),
                "current_bid": self._extract_current_bid(soup),
                "brand": self._extract_brand(soup),
                "model": self._extract_model(soup),
                "upc": self._extract_upc(soup),
                "asin": self._extract_asin(soup),
                "condition": self._extract_condition(soup),
                "damage_notes": self._extract_damage_notes(soup),
                "end_time": self._extract_end_time(soup),
                "seller": self._extract_seller(soup),
                "shipping": self._extract_shipping(soup),
                "returns": self._extract_returns(soup),
                "url": url,
                "scraped_at": datetime.utcnow().isoformat()
            }
            
            # Validate data
            if not self._validate_data(data):
                raise ValueError("Required fields missing from scraped data")
            
            return self._format_output(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            raise
    
    def _extract_lot_number(self, soup: BeautifulSoup) -> str:
        """Extract auction ID from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Auction ID string
        """
        # Try to find in URL first
        url = soup.find("meta", property="og:url")
        if url:
            match = re.search(r"/itm/(\d+)", url.get("content", ""))
            if match:
                return match.group(1)
        
        # Fall back to page content
        item_id = soup.find("div", {"class": "itm-num"})
        if item_id:
            return item_id.text.strip()
        
        raise ValueError("Could not extract auction ID")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Title string
        """
        title = soup.find("h1", {"class": "it-ttl"})
        if title:
            return title.text.strip()
        
        raise ValueError("Could not extract title")
    
    def _extract_current_bid(self, soup: BeautifulSoup) -> float:
        """Extract current bid from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Current bid amount
        """
        bid_elem = soup.find("span", {"class": "prc"})
        if bid_elem:
            bid_text = bid_elem.text.strip()
            # Remove currency symbol and convert to float
            return float(re.sub(r'[^\d.]', '', bid_text))
        
        raise ValueError("Could not extract current bid")
    
    def _extract_brand(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract brand from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Brand string or None if not found
        """
        brand_elem = soup.find("div", {"class": "it-attr", "data-name": "Brand"})
        if brand_elem:
            return brand_elem.find("span", {"class": "attr-value"}).text.strip()
        return None
    
    def _extract_model(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract model from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Model string or None if not found
        """
        model_elem = soup.find("div", {"class": "it-attr", "data-name": "Model"})
        if model_elem:
            return model_elem.find("span", {"class": "attr-value"}).text.strip()
        return None
    
    def _extract_upc(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract UPC from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            UPC string or None if not found
        """
        upc_elem = soup.find("div", {"class": "it-attr", "data-name": "UPC"})
        if upc_elem:
            return upc_elem.find("span", {"class": "attr-value"}).text.strip()
        return None
    
    def _extract_asin(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract ASIN from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            ASIN string or None if not found
        """
        asin_elem = soup.find("div", {"class": "it-attr", "data-name": "ASIN"})
        if asin_elem:
            return asin_elem.find("span", {"class": "attr-value"}).text.strip()
        return None
    
    def _extract_condition(self, soup: BeautifulSoup) -> str:
        """Extract condition from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Condition string
        """
        condition_elem = soup.find("div", {"class": "it-attr", "data-name": "Condition"})
        if condition_elem:
            return condition_elem.find("span", {"class": "attr-value"}).text.strip()
        
        raise ValueError("Could not extract condition")
    
    def _extract_damage_notes(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract damage notes from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Damage notes string or None if not found
        """
        damage_elem = soup.find("div", {"class": "it-attr", "data-name": "Damage"})
        if damage_elem:
            return damage_elem.find("span", {"class": "attr-value"}).text.strip()
        return None
    
    def _extract_end_time(self, soup: BeautifulSoup) -> str:
        """Extract end time from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            End time string in ISO format
        """
        end_time_elem = soup.find("div", {"class": "it-tm"})
        if end_time_elem:
            time_text = end_time_elem.text.strip()
            # Parse eBay time format and convert to ISO
            # Implementation depends on eBay's time format
            return datetime.now().isoformat()  # Placeholder
        return None
    
    def _extract_seller(self, soup: BeautifulSoup) -> Dict:
        """Extract seller information from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary containing seller information
        """
        seller_elem = soup.find("div", {"class": "sllr-info"})
        if seller_elem:
            return {
                "name": seller_elem.find("span", {"class": "sllr-name"}).text.strip(),
                "feedback": seller_elem.find("span", {"class": "sllr-fdbk"}).text.strip(),
                "positive_feedback": float(seller_elem.find("span", {"class": "sllr-pos"}).text.strip().rstrip("%")) / 100
            }
        return None
    
    def _extract_shipping(self, soup: BeautifulSoup) -> Dict:
        """Extract shipping information from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary containing shipping information
        """
        shipping_elem = soup.find("div", {"class": "shp-info"})
        if shipping_elem:
            return {
                "cost": float(re.sub(r'[^\d.]', '', shipping_elem.find("span", {"class": "shp-cost"}).text.strip())),
                "service": shipping_elem.find("span", {"class": "shp-srv"}).text.strip(),
                "location": shipping_elem.find("span", {"class": "shp-loc"}).text.strip()
            }
        return None
    
    def _extract_returns(self, soup: BeautifulSoup) -> Dict:
        """Extract returns information from eBay page.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary containing returns information
        """
        returns_elem = soup.find("div", {"class": "rtn-info"})
        if returns_elem:
            return {
                "accepted": returns_elem.find("span", {"class": "rtn-acc"}).text.strip() == "Yes",
                "time_limit": returns_elem.find("span", {"class": "rtn-tm"}).text.strip(),
                "cost": returns_elem.find("span", {"class": "rtn-cost"}).text.strip()
            }
        return None 