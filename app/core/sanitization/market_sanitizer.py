from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .base_sanitizer import BaseSanitizer

logger = logging.getLogger(__name__)

class MarketSanitizer(BaseSanitizer):
    """Sanitizer for market data."""
    
    def __init__(self):
        """Initialize the market sanitizer."""
        super().__init__()
        
        # Additional field limits
        self.field_limits.update({
            'product_id': 50,
            'brand': 50,
            'model': 50,
            'seller_id': 50
        })
    
    def sanitize_market_data(self, market_data: Dict) -> Dict:
        """Sanitize market data.
        
        Args:
            market_data: Market data to sanitize
            
        Returns:
            Sanitized market data
        """
        try:
            sanitized = {}
            
            # Required fields
            required_fields = ['product_id', 'title', 'price', 'timestamp']
            for field in required_fields:
                if field not in market_data:
                    logger.error(f"Missing required field: {field}")
                    return {}
            
            # Sanitize basic fields
            sanitized['product_id'] = self.prevent_sql_injection(market_data['product_id'])
            sanitized['title'] = self.sanitize_text(market_data['title'], 'title')
            sanitized['description'] = self.sanitize_text(market_data.get('description', ''), 'description')
            sanitized['category'] = self.sanitize_text(market_data.get('category', ''), 'category')
            sanitized['brand'] = self.sanitize_text(market_data.get('brand', ''), 'brand')
            sanitized['model'] = self.sanitize_text(market_data.get('model', ''), 'model')
            
            # Sanitize price
            price = self.sanitize_price(market_data['price'])
            if not price:
                logger.error("Invalid price")
                return {}
            sanitized['price'] = price
            
            # Sanitize timestamp
            timestamp = self.sanitize_date(market_data['timestamp'])
            if not timestamp:
                logger.error("Invalid timestamp")
                return {}
            sanitized['timestamp'] = timestamp
            
            # Sanitize seller info
            if 'seller_id' in market_data:
                sanitized['seller_id'] = self.prevent_sql_injection(market_data['seller_id'])
            
            if 'seller_rating' in market_data:
                try:
                    rating = float(market_data['seller_rating'])
                    if 0 <= rating <= 5:
                        sanitized['seller_rating'] = rating
                except (ValueError, TypeError):
                    pass
            
            # Sanitize sales rank
            if 'sales_rank' in market_data:
                try:
                    rank = int(market_data['sales_rank'])
                    if rank > 0:
                        sanitized['sales_rank'] = rank
                except (ValueError, TypeError):
                    pass
            
            # Sanitize UPC
            if 'upc' in market_data:
                upc = self.sanitize_upc(market_data['upc'])
                if upc:
                    sanitized['upc'] = upc
            
            # Sanitize images
            if 'images' in market_data:
                sanitized_images = []
                for image_url in market_data['images']:
                    if self.verify_image_url(image_url):
                        sanitized_images.append(image_url)
                if sanitized_images:
                    sanitized['images'] = sanitized_images
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Market data sanitization failed: {e}")
            return {}
    
    def validate_price_correlation(self, ebay_price: Decimal, amazon_price: Decimal) -> bool:
        """Validate price correlation between eBay and Amazon.
        
        Args:
            ebay_price: eBay price
            amazon_price: Amazon price
            
        Returns:
            True if prices are within acceptable range
        """
        try:
            # Calculate price difference percentage
            price_diff = abs(ebay_price - amazon_price) / amazon_price
            
            # Check if within 30%
            if price_diff > Decimal('0.30'):
                logger.warning("Price difference too large")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Price correlation validation failed: {e}")
            return False
    
    def validate_sales_rank(self, rank: int) -> bool:
        """Validate sales rank.
        
        Args:
            rank: Sales rank to validate
            
        Returns:
            True if valid
        """
        try:
            # Check if rank is reasonable
            if rank > 1000000:
                logger.warning("Sales rank too high")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Sales rank validation failed: {e}")
            return False
    
    def validate_data_age(self, timestamp: datetime, max_age_days: int = 90) -> bool:
        """Validate data age.
        
        Args:
            timestamp: Data timestamp
            max_age_days: Maximum age in days
            
        Returns:
            True if data is recent enough
        """
        try:
            # Calculate age
            age = datetime.now() - timestamp
            
            # Check if within limit
            if age > timedelta(days=max_age_days):
                logger.warning(f"Data too old: {age.days} days")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Data age validation failed: {e}")
            return False
    
    def validate_price_age(self, timestamp: datetime, max_age_hours: int = 24) -> bool:
        """Validate price age.
        
        Args:
            timestamp: Price timestamp
            max_age_hours: Maximum age in hours
            
        Returns:
            True if price is recent enough
        """
        try:
            # Calculate age
            age = datetime.now() - timestamp
            
            # Check if within limit
            if age > timedelta(hours=max_age_hours):
                logger.warning(f"Price too old: {age.total_seconds() / 3600:.1f} hours")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Price age validation failed: {e}")
            return False 