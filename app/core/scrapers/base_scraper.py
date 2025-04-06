from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime
import re
import time
import random
from pathlib import Path
import json

from src.services.proxy_manager import ProxyManager
from src.services.user_agent_manager import UserAgentManager

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for auction scrapers."""
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None, user_agent_manager: Optional[UserAgentManager] = None):
        """Initialize the scraper.
        
        Args:
            proxy_manager: Optional proxy manager for rotating proxies
            user_agent_manager: Optional user agent manager for rotating user agents
        """
        self.proxy_manager = proxy_manager or ProxyManager()
        self.user_agent_manager = user_agent_manager or UserAgentManager()
        self.name = self.__class__.__name__.lower().replace("scraper", "")
        
        # Load configuration
        self.config = self._load_config()
    
    @abstractmethod
    def scrape_auction(self, auction_id: str, auction_name: Optional[str] = None) -> Dict:
        """Scrape an auction by ID and optional name.
        
        Args:
            auction_id: The auction ID to scrape
            auction_name: Optional auction name for validation
            
        Returns:
            Dictionary containing auction data
        """
        pass
    
    @abstractmethod
    def scrape_auction_by_url(self, url: str) -> Dict:
        """Scrape an auction by URL.
        
        Args:
            url: The auction URL to scrape
            
        Returns:
            Dictionary containing auction data
        """
        pass
    
    def _load_config(self) -> Dict:
        """Load scraper configuration from file.
        
        Returns:
            Dictionary containing configuration
        """
        config_path = Path(__file__).parent / "config" / f"{self.name}_config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                return json.load(f)
        return {}
    
    def _extract_lot_number(self, element) -> str:
        """Extract lot number from element.
        
        Args:
            element: HTML element containing lot number
            
        Returns:
            Extracted lot number
        """
        # Default implementation using XPath
        lot_number = element.xpath("//div[@class='lot-number']/text()")
        if lot_number:
            return lot_number[0].strip()
        return ""
    
    def _extract_title(self, element) -> str:
        """Extract title from element.
        
        Args:
            element: HTML element containing title
            
        Returns:
            Extracted title
        """
        # Default implementation using CSS selector
        title = element.css(".lot-title::text").get()
        if title:
            return title.strip()
        return ""
    
    def _extract_current_bid(self, element) -> float:
        """Extract current bid from element.
        
        Args:
            element: HTML element containing current bid
            
        Returns:
            Extracted current bid as float
        """
        # Default implementation using regex
        bid_text = element.get()
        match = re.search(r'\$(\d+\.\d{2})', bid_text)
        if match:
            return float(match.group(1))
        return 0.0
    
    def _extract_brand(self, element) -> str:
        """Extract brand from element using multiple methods.
        
        Args:
            element: HTML element containing brand information
            
        Returns:
            Extracted brand
        """
        # Method A: From description
        description = element.css(".lot-description::text").get()
        if description:
            match = re.search(r'Brand:\s*([^\n]+)', description)
            if match:
                return match.group(1).strip()
        
        # Method B: NLP extraction from title (placeholder)
        title = self._extract_title(element)
        if title:
            # TODO: Implement NLP extraction
            pass
        
        # Method C: UPC database lookup (placeholder)
        upc = self._extract_upc(element)
        if upc:
            # TODO: Implement UPC lookup
            pass
        
        return ""
    
    def _extract_model(self, element) -> str:
        """Extract model from element using multiple methods.
        
        Args:
            element: HTML element containing model information
            
        Returns:
            Extracted model
        """
        # Method A: From description
        description = element.css(".lot-description::text").get()
        if description:
            match = re.search(r'Model:\s*([^\n]+)', description)
            if match:
                return match.group(1).strip()
        
        # Method B: NLP extraction from title (placeholder)
        title = self._extract_title(element)
        if title:
            # TODO: Implement NLP extraction
            pass
        
        # Method C: UPC database lookup (placeholder)
        upc = self._extract_upc(element)
        if upc:
            # TODO: Implement UPC lookup
            pass
        
        # Method D: Amazon ASIN cross-reference (placeholder)
        asin = self._extract_asin(element)
        if asin:
            # TODO: Implement ASIN lookup
            pass
        
        return ""
    
    def _extract_upc(self, element) -> str:
        """Extract UPC from element.
        
        Args:
            element: HTML element containing UPC
            
        Returns:
            Extracted UPC
        """
        # Default implementation
        description = element.css(".lot-description::text").get()
        if description:
            match = re.search(r'UPC:\s*(\d+)', description)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_asin(self, element) -> str:
        """Extract ASIN from element.
        
        Args:
            element: HTML element containing ASIN
            
        Returns:
            Extracted ASIN
        """
        # Default implementation
        description = element.css(".lot-description::text").get()
        if description:
            match = re.search(r'ASIN:\s*([A-Z0-9]{10})', description)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_condition(self, element) -> str:
        """Extract condition from element.
        
        Args:
            element: HTML element containing condition
            
        Returns:
            Extracted condition
        """
        # Default implementation
        description = element.css(".lot-description::text").get()
        if description:
            match = re.search(r'Condition:\s*([^\n]+)', description)
            if match:
                return match.group(1).strip()
        return ""
    
    def _extract_damage_notes(self, element) -> List[str]:
        """Extract damage notes from element.
        
        Args:
            element: HTML element containing damage notes
            
        Returns:
            List of extracted damage notes
        """
        # Default implementation
        description = element.css(".lot-description::text").get()
        if description:
            match = re.search(r'Damage Notes:\s*([^\n]+)', description)
            if match:
                return [note.strip() for note in match.group(1).split(",")]
        return []
    
    def _handle_captcha(self, response) -> bool:
        """Handle CAPTCHA detection.
        
        Args:
            response: HTTP response
            
        Returns:
            True if CAPTCHA was handled, False otherwise
        """
        # Check for CAPTCHA indicators
        if "captcha" in response.text.lower() or "robot" in response.text.lower():
            logger.warning("CAPTCHA detected, rotating proxy")
            self.proxy_manager.rotate_proxy()
            return True
        return False
    
    def _validate_data(self, data: Dict) -> bool:
        """Validate scraped data.
        
        Args:
            data: Dictionary containing scraped data
            
        Returns:
            True if data is valid, False otherwise
        """
        # Check required fields
        required_fields = ["lot_number", "title", "current_bid"]
        for field in required_fields:
            if not data.get(field):
                logger.error(f"Missing required field: {field}")
                return False
        
        return True
    
    def _format_output(self, auction_id: str, auction_name: str, items: List[Dict]) -> Dict:
        """Format scraped data into output structure.
        
        Args:
            auction_id: The auction ID
            auction_name: The auction name
            items: List of scraped items
            
        Returns:
            Formatted output dictionary
        """
        return {
            "auction_meta": {
                "id": auction_id,
                "name": auction_name,
                "end_time": datetime.utcnow().isoformat(),  # TODO: Extract actual end time
            },
            "items": items
        }
    
    def _delay(self, seconds: float) -> None:
        """Apply delay between requests.
        
        Args:
            seconds: Number of seconds to delay
        """
        time.sleep(seconds)
    
    def _get_random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> float:
        """Get random delay between min and max seconds.
        
        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
            
        Returns:
            Random delay in seconds
        """
        return random.uniform(min_seconds, max_seconds) 