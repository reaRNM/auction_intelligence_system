from typing import Dict, List, Optional
import logging
import os
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

from .base_research import BaseResearch

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EbayResearch(BaseResearch):
    """eBay Terapeak research service."""
    
    def __init__(self):
        """Initialize the eBay research service."""
        super().__init__()
        self.api_key = os.getenv("EBAY_API_KEY")
        self.terapeak_key = os.getenv("TERAPEAK_API_KEY")
        self.base_url = "https://api.ebay.com"
        self.terapeak_url = "https://api.terapeak.com"
    
    def get_ebay_data(self, item_id: str) -> Dict:
        """Get eBay Terapeak data.
        
        Args:
            item_id: eBay item ID
            
        Returns:
            Dictionary containing eBay data
        """
        try:
            # Get sold items data
            sold_data = self._get_sold_items(item_id)
            
            # Get active listings data
            active_data = self._get_active_listings(item_id)
            
            # Get watcher analysis
            watcher_data = self._get_watcher_analysis(item_id)
            
            return {
                "sold_stats": {
                    "90d_volume": sold_data.get("volume", 0),
                    "avg_price": sold_data.get("avg_price", 0.0),
                    "price_distribution": sold_data.get("price_distribution", [])
                },
                "active_listings": {
                    "count": active_data.get("count", 0),
                    "watchers_total": watcher_data.get("total_watchers", 0),
                    "promoted_pct": watcher_data.get("promoted_percentage", 0.0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get eBay data for item {item_id}: {e}")
            return {}
    
    def _get_sold_items(self, item_id: str) -> Dict:
        """Get sold items data from Terapeak.
        
        Args:
            item_id: eBay item ID
            
        Returns:
            Dictionary containing sold items data
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.terapeak_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "item_id": item_id,
                "days": 90,
                "include_details": True
            }
            
            response = requests.get(
                f"{self.terapeak_url}/sold-items",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract prices and trim outliers
            prices = [item["price"] for item in data.get("items", [])]
            valid_prices = self.trim_outliers(prices)
            
            # Calculate price distribution
            if valid_prices:
                min_price = min(valid_prices)
                max_price = max(valid_prices)
                step = (max_price - min_price) / 2
                distribution = [
                    min_price,
                    sum(valid_prices) / len(valid_prices),
                    max_price
                ]
            else:
                distribution = [0, 0, 0]
            
            return {
                "volume": len(valid_prices),
                "avg_price": sum(valid_prices) / len(valid_prices) if valid_prices else 0.0,
                "price_distribution": distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get sold items data for item {item_id}: {e}")
            return {"volume": 0, "avg_price": 0.0, "price_distribution": [0, 0, 0]}
    
    def _get_active_listings(self, item_id: str) -> Dict:
        """Get active listings data from Terapeak.
        
        Args:
            item_id: eBay item ID
            
        Returns:
            Dictionary containing active listings data
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.terapeak_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "item_id": item_id,
                "include_details": True
            }
            
            response = requests.get(
                f"{self.terapeak_url}/active-listings",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return {"count": len(data.get("items", []))}
            
        except Exception as e:
            logger.error(f"Failed to get active listings data for item {item_id}: {e}")
            return {"count": 0}
    
    def _get_watcher_analysis(self, item_id: str) -> Dict:
        """Get watcher analysis data from Terapeak.
        
        Args:
            item_id: eBay item ID
            
        Returns:
            Dictionary containing watcher analysis data
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.terapeak_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "item_id": item_id,
                "include_details": True
            }
            
            response = requests.get(
                f"{self.terapeak_url}/watcher-analysis",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculate total watchers and promoted percentage
            total_watchers = sum(item["watchers"] for item in data.get("items", []))
            promoted_items = sum(1 for item in data.get("items", []) if item.get("is_promoted"))
            total_items = len(data.get("items", []))
            
            promoted_percentage = (promoted_items / total_items * 100) if total_items > 0 else 0.0
            
            return {
                "total_watchers": total_watchers,
                "promoted_percentage": promoted_percentage
            }
            
        except Exception as e:
            logger.error(f"Failed to get watcher analysis data for item {item_id}: {e}")
            return {"total_watchers": 0, "promoted_percentage": 0.0} 