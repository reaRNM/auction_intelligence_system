from typing import Any, Dict, List, Optional, Union
import re
import html
import unicodedata
from decimal import Decimal
import logging
from datetime import datetime, timedelta
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class BaseSanitizer:
    """Base class for data sanitization."""
    
    def __init__(self):
        """Initialize the sanitizer."""
        # Common regex patterns
        self.price_pattern = re.compile(r'^\d+(\.\d{1,2})?$')
        self.upc_pattern = re.compile(r'^\d{12,13}$')
        self.html_pattern = re.compile(r'<[^>]+>')
        
        # Field length limits
        self.field_limits = {
            'title': 80,
            'description': 5000,
            'category': 100,
            'brand': 50,
            'model': 50,
            'condition': 20
        }
    
    def sanitize_text(self, text: str, field: str) -> str:
        """Sanitize text input.
        
        Args:
            text: Text to sanitize
            field: Field name for length limit
            
        Returns:
            Sanitized text
        """
        try:
            if not text:
                return ""
            
            # Strip HTML tags
            text = self.html_pattern.sub('', text)
            
            # Decode HTML entities
            text = html.unescape(text)
            
            # Normalize Unicode
            text = unicodedata.normalize('NFKC', text)
            
            # Truncate to field limit
            limit = self.field_limits.get(field, 1000)
            if len(text) > limit:
                text = text[:limit]
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Text sanitization failed: {e}")
            return ""
    
    def sanitize_price(self, price: Union[str, float, Decimal]) -> Optional[Decimal]:
        """Sanitize price value.
        
        Args:
            price: Price to sanitize
            
        Returns:
            Sanitized Decimal price or None if invalid
        """
        try:
            # Convert to string
            if isinstance(price, (float, Decimal)):
                price = str(price)
            
            # Validate format
            if not self.price_pattern.match(price):
                return None
            
            # Convert to Decimal
            price_decimal = Decimal(price)
            
            # Validate range
            if price_decimal <= 0 or price_decimal > 1000000:
                return None
            
            return price_decimal
            
        except Exception as e:
            logger.error(f"Price sanitization failed: {e}")
            return None
    
    def sanitize_upc(self, upc: str) -> Optional[str]:
        """Sanitize UPC code.
        
        Args:
            upc: UPC to sanitize
            
        Returns:
            Sanitized UPC or None if invalid
        """
        try:
            # Remove non-digits
            upc = re.sub(r'\D', '', upc)
            
            # Validate format
            if not self.upc_pattern.match(upc):
                return None
            
            return upc
            
        except Exception as e:
            logger.error(f"UPC sanitization failed: {e}")
            return None
    
    def verify_image_url(self, url: str) -> bool:
        """Verify image URL.
        
        Args:
            url: URL to verify
            
        Returns:
            True if valid image URL
        """
        try:
            # Parse URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Check content type
            response = requests.head(url, timeout=5)
            content_type = response.headers.get('content-type', '')
            
            return content_type.startswith('image/')
            
        except Exception as e:
            logger.error(f"Image URL verification failed: {e}")
            return False
    
    def sanitize_date(self, date: Union[str, datetime]) -> Optional[datetime]:
        """Sanitize date value.
        
        Args:
            date: Date to sanitize
            
        Returns:
            Sanitized datetime or None if invalid
        """
        try:
            # Convert string to datetime
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            
            # Validate range
            if date > datetime.now():
                return None
            
            return date
            
        except Exception as e:
            logger.error(f"Date sanitization failed: {e}")
            return None
    
    def sanitize_enum(self, value: str, valid_values: List[str]) -> Optional[str]:
        """Sanitize enumeration value.
        
        Args:
            value: Value to sanitize
            valid_values: List of valid values
            
        Returns:
            Sanitized value or None if invalid
        """
        try:
            # Normalize value
            value = value.strip().lower()
            
            # Check if valid
            if value in [v.lower() for v in valid_values]:
                return value
            
            return None
            
        except Exception as e:
            logger.error(f"Enumeration sanitization failed: {e}")
            return None
    
    def prevent_sql_injection(self, value: str) -> str:
        """Prevent SQL injection.
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized value
        """
        try:
            # Remove SQL keywords
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION']
            value = value.upper()
            for keyword in sql_keywords:
                value = value.replace(keyword, '')
            
            # Remove special characters
            value = re.sub(r'[\'";\\]', '', value)
            
            return value
            
        except Exception as e:
            logger.error(f"SQL injection prevention failed: {e}")
            return "" 