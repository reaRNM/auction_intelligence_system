from typing import Dict, List, Optional, Union
import logging
from decimal import Decimal

from .base_sanitizer import BaseSanitizer

logger = logging.getLogger(__name__)

class UserSanitizer(BaseSanitizer):
    """Sanitizer for user input."""
    
    def __init__(self):
        """Initialize the user input sanitizer."""
        super().__init__()
        
        # Additional field limits
        self.field_limits.update({
            'username': 50,
            'email': 100,
            'phone': 20,
            'address': 200,
            'city': 100,
            'state': 2,
            'zip': 10
        })
        
        # Valid categories
        self.valid_categories = [
            'Antiques',
            'Art',
            'Books',
            'Collectibles',
            'Electronics',
            'Fashion',
            'Home',
            'Jewelry',
            'Sports',
            'Toys',
            'Other'
        ]
    
    def sanitize_user_input(self, user_input: Dict) -> Dict:
        """Sanitize user input.
        
        Args:
            user_input: User input to sanitize
            
        Returns:
            Sanitized user input
        """
        try:
            sanitized = {}
            
            # Required fields
            required_fields = ['username', 'email']
            for field in required_fields:
                if field not in user_input:
                    logger.error(f"Missing required field: {field}")
                    return {}
            
            # Sanitize basic fields
            sanitized['username'] = self.prevent_sql_injection(user_input['username'])
            sanitized['email'] = self.sanitize_text(user_input['email'], 'email')
            
            # Sanitize optional fields
            if 'phone' in user_input:
                sanitized['phone'] = self.sanitize_text(user_input['phone'], 'phone')
            
            if 'address' in user_input:
                sanitized['address'] = self.sanitize_text(user_input['address'], 'address')
            
            if 'city' in user_input:
                sanitized['city'] = self.sanitize_text(user_input['city'], 'city')
            
            if 'state' in user_input:
                sanitized['state'] = self.sanitize_text(user_input['state'], 'state')
            
            if 'zip' in user_input:
                sanitized['zip'] = self.sanitize_text(user_input['zip'], 'zip')
            
            # Sanitize preferences
            if 'preferences' in user_input:
                preferences = user_input['preferences']
                sanitized_preferences = {}
                
                # Sanitize categories
                if 'categories' in preferences:
                    categories = []
                    for category in preferences['categories']:
                        sanitized_category = self.sanitize_enum(category, self.valid_categories)
                        if sanitized_category:
                            categories.append(sanitized_category)
                    if categories:
                        sanitized_preferences['categories'] = categories
                
                # Sanitize price range
                if 'min_price' in preferences:
                    min_price = self.sanitize_price(preferences['min_price'])
                    if min_price:
                        sanitized_preferences['min_price'] = min_price
                
                if 'max_price' in preferences:
                    max_price = self.sanitize_price(preferences['max_price'])
                    if max_price:
                        sanitized_preferences['max_price'] = max_price
                
                # Sanitize condition preferences
                if 'conditions' in preferences:
                    conditions = []
                    for condition in preferences['conditions']:
                        sanitized_condition = self.sanitize_text(condition, 'condition')
                        if sanitized_condition:
                            conditions.append(sanitized_condition)
                    if conditions:
                        sanitized_preferences['conditions'] = conditions
                
                if sanitized_preferences:
                    sanitized['preferences'] = sanitized_preferences
            
            return sanitized
            
        except Exception as e:
            logger.error(f"User input sanitization failed: {e}")
            return {}
    
    def validate_price_range(self, min_price: Optional[Decimal], max_price: Optional[Decimal]) -> bool:
        """Validate price range.
        
        Args:
            min_price: Minimum price
            max_price: Maximum price
            
        Returns:
            True if valid
        """
        try:
            # Check if both prices are provided
            if min_price is None or max_price is None:
                return True
            
            # Check if min is less than max
            if min_price > max_price:
                logger.warning("Minimum price cannot be greater than maximum price")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Price range validation failed: {e}")
            return False
    
    def validate_email(self, email: str) -> bool:
        """Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            True if valid
        """
        try:
            # Basic email format check
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                logger.warning("Invalid email format")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Email validation failed: {e}")
            return False
    
    def validate_phone(self, phone: str) -> bool:
        """Validate phone number format.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid
        """
        try:
            # Remove non-digits
            digits = re.sub(r'\D', '', phone)
            
            # Check length
            if len(digits) < 10 or len(digits) > 15:
                logger.warning("Invalid phone number length")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Phone validation failed: {e}")
            return False
    
    def validate_zip(self, zip_code: str) -> bool:
        """Validate ZIP code format.
        
        Args:
            zip_code: ZIP code to validate
            
        Returns:
            True if valid
        """
        try:
            # Remove non-digits
            digits = re.sub(r'\D', '', zip_code)
            
            # Check length
            if len(digits) != 5:
                logger.warning("Invalid ZIP code length")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"ZIP code validation failed: {e}")
            return False 