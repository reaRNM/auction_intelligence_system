from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .base_sanitizer import BaseSanitizer

logger = logging.getLogger(__name__)

class AuctionSanitizer(BaseSanitizer):
    """Sanitizer for auction data."""
    
    def __init__(self):
        """Initialize the auction sanitizer."""
        super().__init__()
        
        # Additional field limits
        self.field_limits.update({
            'auction_id': 50,
            'seller_id': 50,
            'location': 100,
            'shipping_info': 500
        })
    
    def sanitize_auction(self, auction_data: Dict) -> Dict:
        """Sanitize auction data.
        
        Args:
            auction_data: Auction data to sanitize
            
        Returns:
            Sanitized auction data
        """
        try:
            sanitized = {}
            
            # Required fields
            required_fields = ['auction_id', 'title', 'current_bid', 'end_time']
            for field in required_fields:
                if field not in auction_data:
                    logger.error(f"Missing required field: {field}")
                    return {}
            
            # Sanitize basic fields
            sanitized['auction_id'] = self.prevent_sql_injection(auction_data['auction_id'])
            sanitized['title'] = self.sanitize_text(auction_data['title'], 'title')
            sanitized['description'] = self.sanitize_text(auction_data.get('description', ''), 'description')
            sanitized['category'] = self.sanitize_text(auction_data.get('category', ''), 'category')
            sanitized['condition'] = self.sanitize_text(auction_data.get('condition', ''), 'condition')
            
            # Sanitize price fields
            current_bid = self.sanitize_price(auction_data['current_bid'])
            if not current_bid:
                logger.error("Invalid current bid")
                return {}
            sanitized['current_bid'] = current_bid
            
            if 'buy_it_now' in auction_data:
                buy_it_now = self.sanitize_price(auction_data['buy_it_now'])
                if buy_it_now:
                    sanitized['buy_it_now'] = buy_it_now
            
            # Sanitize dates
            end_time = self.sanitize_date(auction_data['end_time'])
            if not end_time:
                logger.error("Invalid end time")
                return {}
            sanitized['end_time'] = end_time
            
            if 'start_time' in auction_data:
                start_time = self.sanitize_date(auction_data['start_time'])
                if start_time:
                    sanitized['start_time'] = start_time
            
            # Sanitize seller info
            if 'seller_id' in auction_data:
                sanitized['seller_id'] = self.prevent_sql_injection(auction_data['seller_id'])
            
            if 'seller_rating' in auction_data:
                try:
                    rating = float(auction_data['seller_rating'])
                    if 0 <= rating <= 5:
                        sanitized['seller_rating'] = rating
                except (ValueError, TypeError):
                    pass
            
            # Sanitize location
            if 'location' in auction_data:
                sanitized['location'] = self.sanitize_text(auction_data['location'], 'location')
            
            # Sanitize shipping info
            if 'shipping_info' in auction_data:
                sanitized['shipping_info'] = self.sanitize_text(auction_data['shipping_info'], 'shipping_info')
            
            # Sanitize UPC
            if 'upc' in auction_data:
                upc = self.sanitize_upc(auction_data['upc'])
                if upc:
                    sanitized['upc'] = upc
            
            # Sanitize images
            if 'images' in auction_data:
                sanitized_images = []
                for image_url in auction_data['images']:
                    if self.verify_image_url(image_url):
                        sanitized_images.append(image_url)
                if sanitized_images:
                    sanitized['images'] = sanitized_images
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Auction sanitization failed: {e}")
            return {}
    
    def validate_bid(self, bid: Union[str, float, Decimal], current_bid: Decimal) -> Optional[Decimal]:
        """Validate bid amount.
        
        Args:
            bid: Bid amount to validate
            current_bid: Current bid amount
            
        Returns:
            Validated bid amount or None if invalid
        """
        try:
            # Sanitize bid
            bid_decimal = self.sanitize_price(bid)
            if not bid_decimal:
                return None
            
            # Validate against current bid
            if bid_decimal <= current_bid:
                logger.warning("Bid must be higher than current bid")
                return None
            
            # Validate increment
            min_increment = Decimal('0.50')
            if bid_decimal - current_bid < min_increment:
                logger.warning("Bid increment too small")
                return None
            
            return bid_decimal
            
        except Exception as e:
            logger.error(f"Bid validation failed: {e}")
            return None
    
    def validate_auction_time(self, end_time: datetime) -> bool:
        """Validate auction end time.
        
        Args:
            end_time: Auction end time
            
        Returns:
            True if valid
        """
        try:
            # Check if in future
            if end_time <= datetime.now():
                logger.warning("Auction end time must be in the future")
                return False
            
            # Check if within reasonable range (e.g., 30 days)
            max_duration = timedelta(days=30)
            if end_time > datetime.now() + max_duration:
                logger.warning("Auction duration too long")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Auction time validation failed: {e}")
            return False 