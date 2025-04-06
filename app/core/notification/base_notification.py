from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    """Priority levels for notifications."""
    CRITICAL = 0  # Bid failures, system errors
    HIGH = 1      # Opportunity alerts, price drops
    MEDIUM = 2    # System updates, research completed
    LOW = 3       # Analytics, trends

class NotificationType(Enum):
    """Types of notifications."""
    # Auction Alerts
    NEW_AUCTION = "new_auction"
    ENDING_SOON = "ending_soon"
    PRICE_MOVEMENT = "price_movement"
    
    # System Events
    RESEARCH_COMPLETED = "research_completed"
    LISTING_PUBLISHED = "listing_published"
    ERROR_CONDITION = "error_condition"
    
    # Market Intelligence
    PRICE_DROP = "price_drop"
    COMPETITOR_LISTING = "competitor_listing"
    CATEGORY_TREND = "category_trend"

class DeliveryMethod(Enum):
    """Delivery methods for notifications."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    TOAST = "toast"

class BaseNotification:
    """Base class for all notifications."""
    
    def __init__(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None,
        recipient_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        """Initialize a notification.
        
        Args:
            notification_type: Type of notification
            priority: Priority level
            title: Notification title
            message: Notification message
            data: Additional data for the notification
            delivery_methods: List of delivery methods
            recipient_id: ID of the recipient
            created_at: Creation timestamp
        """
        self.notification_type = notification_type
        self.priority = priority
        self.title = title
        self.message = message
        self.data = data or {}
        self.delivery_methods = delivery_methods or [DeliveryMethod.TOAST]
        self.recipient_id = recipient_id
        self.created_at = created_at or datetime.now()
        self.delivered = False
        self.delivery_timestamps = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary.
        
        Returns:
            Dictionary representation of the notification
        """
        return {
            'notification_type': self.notification_type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'delivery_methods': [method.value for method in self.delivery_methods],
            'recipient_id': self.recipient_id,
            'created_at': self.created_at.isoformat(),
            'delivered': self.delivered,
            'delivery_timestamps': {
                method: timestamp.isoformat() 
                for method, timestamp in self.delivery_timestamps.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseNotification':
        """Create notification from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Notification instance
        """
        return cls(
            notification_type=NotificationType(data['notification_type']),
            priority=NotificationPriority(data['priority']),
            title=data['title'],
            message=data['message'],
            data=data.get('data', {}),
            delivery_methods=[DeliveryMethod(method) for method in data.get('delivery_methods', [])],
            recipient_id=data.get('recipient_id'),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else None
        )
    
    def mark_delivered(self, method: DeliveryMethod) -> None:
        """Mark notification as delivered via a specific method.
        
        Args:
            method: Delivery method
        """
        self.delivery_timestamps[method] = datetime.now()
        
        # Check if all delivery methods have been completed
        if all(method in self.delivery_timestamps for method in self.delivery_methods):
            self.delivered = True
            logger.info(f"Notification {self.notification_type.value} fully delivered to {self.recipient_id}")
    
    def __str__(self) -> str:
        """String representation of the notification.
        
        Returns:
            String representation
        """
        return f"{self.notification_type.value} ({self.priority.name}): {self.title}" 