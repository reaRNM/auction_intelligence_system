from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.services.database import get_db
from src.services.models import Item

logger = logging.getLogger(__name__)

class BaseResearch(ABC):
    """Base class for product research services."""
    
    def __init__(self):
        """Initialize the research service."""
        self.db = next(get_db())
    
    def check_database(self, upc: Optional[str] = None, brand: Optional[str] = None,
                      model: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        """Check database for similar items.
        
        Args:
            upc: Optional UPC to search for
            brand: Optional brand name
            model: Optional model name
            category: Optional category
            
        Returns:
            List of similar items from database
        """
        try:
            query = """
                SELECT * FROM items 
                WHERE (upc = :upc 
                    OR (similarity(brand, :brand) > 0.85 
                        AND similarity(model, :model) > 0.85
                        AND category LIKE :category))
                AND created_at > :recency
            """
            
            params = {
                "upc": upc,
                "brand": brand,
                "model": model,
                "category": f"%{category}%" if category else "%",
                "recency": datetime.utcnow() - timedelta(days=30)
            }
            
            result = self.db.execute(text(query), params)
            return [dict(row) for row in result]
            
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return []
    
    @abstractmethod
    def get_amazon_data(self, asin: str) -> Dict:
        """Get Amazon product data.
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            Dictionary containing Amazon data
        """
        pass
    
    @abstractmethod
    def get_ebay_data(self, item_id: str) -> Dict:
        """Get eBay Terapeak data.
        
        Args:
            item_id: eBay item ID
            
        Returns:
            Dictionary containing eBay data
        """
        pass
    
    def validate_price(self, price: float, prices: List[float]) -> bool:
        """Validate if a price is within acceptable range.
        
        Args:
            price: Price to validate
            prices: List of historical prices
            
        Returns:
            True if price is valid, False otherwise
        """
        if not prices:
            return True
            
        median = np.median(prices)
        std_dev = np.std(prices)
        
        return abs(price - median) <= 3 * std_dev
    
    def trim_outliers(self, data: List[float], percentile: float = 5.0) -> List[float]:
        """Trim outliers from data using percentile.
        
        Args:
            data: List of values
            percentile: Percentile to trim from top and bottom
            
        Returns:
            Trimmed list of values
        """
        if not data:
            return []
            
        lower = np.percentile(data, percentile)
        upper = np.percentile(data, 100 - percentile)
        
        return [x for x in data if lower <= x <= upper]
    
    def calculate_weighted_average(self, values: List[float], weights: List[float]) -> float:
        """Calculate weighted average of values.
        
        Args:
            values: List of values
            weights: List of weights
            
        Returns:
            Weighted average
        """
        if not values or not weights or len(values) != len(weights):
            return 0.0
            
        return np.average(values, weights=weights)
    
    def format_output(self, amazon_data: Dict, ebay_data: Dict) -> Dict:
        """Format research data into output structure.
        
        Args:
            amazon_data: Amazon research data
            ebay_data: eBay research data
            
        Returns:
            Formatted output dictionary
        """
        return {
            "amazon_data": amazon_data,
            "ebay_data": ebay_data
        } 