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

class AmazonResearch(BaseResearch):
    """Amazon-specific research service."""
    
    def __init__(self):
        """Initialize the Amazon research service."""
        super().__init__()
        self.api_key = os.getenv("AMAZON_API_KEY")
        self.keepa_key = os.getenv("KEEPA_API_KEY")
        self.base_url = "https://api.amazon.com"
        self.keepa_url = "https://api.keepa.com"
    
    def get_amazon_data(self, asin: str) -> Dict:
        """Get Amazon product data.
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            Dictionary containing Amazon data
        """
        try:
            # Get current price and rating
            product_data = self._get_product_data(asin)
            if not product_data:
                return {}
            
            # Get price history from Keepa
            price_history = self._get_price_history(asin)
            
            # Get sales rank data
            sales_rank = self._get_sales_rank(asin)
            
            # Calculate sales velocity
            velocity = self._calculate_sales_velocity(sales_rank)
            
            # Calculate return risk
            return_risk = self._calculate_return_risk(product_data)
            
            return {
                "current_price": product_data.get("price", 0.0),
                "price_history": {
                    "30d_avg": price_history.get("30d_avg", 0.0),
                    "30d_low": price_history.get("30d_low", 0.0)
                },
                "sales_velocity": velocity,
                "return_risk": return_risk
            }
            
        except Exception as e:
            logger.error(f"Failed to get Amazon data for ASIN {asin}: {e}")
            return {}
    
    def _get_product_data(self, asin: str) -> Dict:
        """Get current product data from Amazon API.
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            Dictionary containing product data
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.base_url}/products/{asin}",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Validate price
            if not self.validate_price(data["price"], [data["price"]]):
                logger.warning(f"Price validation failed for ASIN {asin}")
                return {}
            
            # Verify stock status
            if data.get("stock_status") != "In Stock":
                logger.warning(f"Product {asin} is not in stock")
                return {}
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to get product data for ASIN {asin}: {e}")
            return {}
    
    def _get_price_history(self, asin: str) -> Dict:
        """Get price history from Keepa API.
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            Dictionary containing price history
        """
        try:
            params = {
                "key": self.keepa_key,
                "domain": 1,  # Amazon.com
                "asin": asin,
                "stats": 1
            }
            
            response = requests.get(
                f"{self.keepa_url}/product",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract 30-day price statistics
            prices = data.get("prices", [])
            recent_prices = [p for p in prices if p["date"] > datetime.utcnow() - timedelta(days=30)]
            
            if not recent_prices:
                return {"30d_avg": 0.0, "30d_low": 0.0}
            
            # Trim outliers
            valid_prices = self.trim_outliers([p["price"] for p in recent_prices])
            
            return {
                "30d_avg": sum(valid_prices) / len(valid_prices) if valid_prices else 0.0,
                "30d_low": min(valid_prices) if valid_prices else 0.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get price history for ASIN {asin}: {e}")
            return {"30d_avg": 0.0, "30d_low": 0.0}
    
    def _get_sales_rank(self, asin: str) -> List[Dict]:
        """Get sales rank history.
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            List of sales rank data points
        """
        try:
            params = {
                "key": self.keepa_key,
                "domain": 1,
                "asin": asin,
                "stats": 1
            }
            
            response = requests.get(
                f"{self.keepa_url}/product",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("sales_rank", [])
            
        except Exception as e:
            logger.error(f"Failed to get sales rank for ASIN {asin}: {e}")
            return []
    
    def _calculate_sales_velocity(self, sales_rank: List[Dict]) -> str:
        """Calculate sales velocity based on sales rank history.
        
        Args:
            sales_rank: List of sales rank data points
            
        Returns:
            Sales velocity category (High/Medium/Low)
        """
        if not sales_rank:
            return "Unknown"
        
        # Calculate average daily rank change
        rank_changes = []
        for i in range(1, len(sales_rank)):
            change = sales_rank[i]["rank"] - sales_rank[i-1]["rank"]
            rank_changes.append(change)
        
        avg_change = sum(rank_changes) / len(rank_changes) if rank_changes else 0
        
        if avg_change > 100:
            return "High"
        elif avg_change > 50:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_return_risk(self, product_data: Dict) -> str:
        """Calculate return risk based on product data.
        
        Args:
            product_data: Product data from Amazon API
            
        Returns:
            Return risk category with percentage
        """
        # Simple risk calculation based on rating and review count
        rating = product_data.get("rating", 0.0)
        review_count = product_data.get("review_count", 0)
        
        if rating < 3.5 and review_count > 100:
            return "High (25%)"
        elif rating < 4.0 and review_count > 50:
            return "Medium (12%)"
        else:
            return "Low (5%)" 