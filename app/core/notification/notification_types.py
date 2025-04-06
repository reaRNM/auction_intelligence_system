from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime, timedelta

from .base_notification import BaseNotification, NotificationPriority, NotificationType, DeliveryMethod

logger = logging.getLogger(__name__)

# Auction Alert Notifications

class NewAuctionNotification(BaseNotification):
    """Notification for new matching auctions."""
    
    def __init__(
        self,
        auction_id: str,
        title: str,
        current_price: float,
        estimated_value: float,
        end_time: datetime,
        category: str,
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a new auction notification.
        
        Args:
            auction_id: ID of the auction
            title: Auction title
            current_price: Current price
            estimated_value: Estimated value
            end_time: Auction end time
            category: Auction category
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Calculate potential profit
        potential_profit = estimated_value - current_price
        profit_percentage = (potential_profit / current_price) * 100 if current_price > 0 else 0
        
        # Determine priority based on profit potential
        if profit_percentage >= 50:
            priority = NotificationPriority.HIGH
        elif profit_percentage >= 25:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW
        
        # Create message
        message = (
            f"New auction matching your criteria: {title}\n"
            f"Current price: ${current_price:.2f}\n"
            f"Estimated value: ${estimated_value:.2f}\n"
            f"Potential profit: ${potential_profit:.2f} ({profit_percentage:.1f}%)\n"
            f"Ends: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Create data dictionary
        data = {
            'auction_id': auction_id,
            'title': title,
            'current_price': current_price,
            'estimated_value': estimated_value,
            'potential_profit': potential_profit,
            'profit_percentage': profit_percentage,
            'end_time': end_time.isoformat(),
            'category': category,
            'action_url': f"/auctions/{auction_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.NEW_AUCTION,
            priority=priority,
            title=f"New Auction: {title}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

class EndingSoonNotification(BaseNotification):
    """Notification for auctions ending soon."""
    
    def __init__(
        self,
        auction_id: str,
        title: str,
        current_price: float,
        estimated_value: float,
        end_time: datetime,
        category: str,
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize an ending soon notification.
        
        Args:
            auction_id: ID of the auction
            title: Auction title
            current_price: Current price
            estimated_value: Estimated value
            end_time: Auction end time
            category: Auction category
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Calculate time until end
        time_until_end = end_time - datetime.now()
        minutes_until_end = time_until_end.total_seconds() / 60
        
        # Calculate potential profit
        potential_profit = estimated_value - current_price
        profit_percentage = (potential_profit / current_price) * 100 if current_price > 0 else 0
        
        # Determine priority based on profit potential and time until end
        if minutes_until_end <= 15 and profit_percentage >= 25:
            priority = NotificationPriority.CRITICAL
        elif minutes_until_end <= 30 and profit_percentage >= 15:
            priority = NotificationPriority.HIGH
        else:
            priority = NotificationPriority.MEDIUM
        
        # Create message
        message = (
            f"Auction ending soon: {title}\n"
            f"Current price: ${current_price:.2f}\n"
            f"Estimated value: ${estimated_value:.2f}\n"
            f"Potential profit: ${potential_profit:.2f} ({profit_percentage:.1f}%)\n"
            f"Ends in: {int(minutes_until_end)} minutes"
        )
        
        # Create data dictionary
        data = {
            'auction_id': auction_id,
            'title': title,
            'current_price': current_price,
            'estimated_value': estimated_value,
            'potential_profit': potential_profit,
            'profit_percentage': profit_percentage,
            'end_time': end_time.isoformat(),
            'minutes_until_end': int(minutes_until_end),
            'category': category,
            'action_url': f"/auctions/{auction_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.ENDING_SOON,
            priority=priority,
            title=f"Auction Ending Soon: {title}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

class PriceMovementNotification(BaseNotification):
    """Notification for significant price movements."""
    
    def __init__(
        self,
        auction_id: str,
        title: str,
        old_price: float,
        new_price: float,
        estimated_value: float,
        end_time: datetime,
        category: str,
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a price movement notification.
        
        Args:
            auction_id: ID of the auction
            title: Auction title
            old_price: Previous price
            new_price: New price
            estimated_value: Estimated value
            end_time: Auction end time
            category: Auction category
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Calculate price change
        price_change = new_price - old_price
        price_change_percentage = (price_change / old_price) * 100 if old_price > 0 else 0
        
        # Calculate potential profit
        potential_profit = estimated_value - new_price
        profit_percentage = (potential_profit / new_price) * 100 if new_price > 0 else 0
        
        # Determine priority based on price change and profit potential
        if abs(price_change_percentage) >= 20 and profit_percentage >= 25:
            priority = NotificationPriority.HIGH
        elif abs(price_change_percentage) >= 10:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW
        
        # Create message
        direction = "increased" if price_change > 0 else "decreased"
        message = (
            f"Price {direction} for: {title}\n"
            f"Previous price: ${old_price:.2f}\n"
            f"New price: ${new_price:.2f}\n"
            f"Change: ${abs(price_change):.2f} ({abs(price_change_percentage):.1f}%)\n"
            f"Estimated value: ${estimated_value:.2f}\n"
            f"Potential profit: ${potential_profit:.2f} ({profit_percentage:.1f}%)\n"
            f"Ends: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Create data dictionary
        data = {
            'auction_id': auction_id,
            'title': title,
            'old_price': old_price,
            'new_price': new_price,
            'price_change': price_change,
            'price_change_percentage': price_change_percentage,
            'estimated_value': estimated_value,
            'potential_profit': potential_profit,
            'profit_percentage': profit_percentage,
            'end_time': end_time.isoformat(),
            'category': category,
            'action_url': f"/auctions/{auction_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.PRICE_MOVEMENT,
            priority=priority,
            title=f"Price {direction.capitalize()} for {title}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

# System Event Notifications

class ResearchCompletedNotification(BaseNotification):
    """Notification for completed research tasks."""
    
    def __init__(
        self,
        research_id: str,
        research_type: str,
        item_count: int,
        findings: Dict[str, Any],
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a research completed notification.
        
        Args:
            research_id: ID of the research task
            research_type: Type of research
            item_count: Number of items researched
            findings: Research findings
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Create message
        message = (
            f"Research task completed: {research_type}\n"
            f"Items analyzed: {item_count}\n"
            f"Summary: {findings.get('summary', 'No summary available')}"
        )
        
        # Create data dictionary
        data = {
            'research_id': research_id,
            'research_type': research_type,
            'item_count': item_count,
            'findings': findings,
            'action_url': f"/research/{research_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.RESEARCH_COMPLETED,
            priority=NotificationPriority.MEDIUM,
            title=f"Research Completed: {research_type}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

class ListingPublishedNotification(BaseNotification):
    """Notification for published listings."""
    
    def __init__(
        self,
        listing_id: str,
        title: str,
        price: float,
        category: str,
        url: str,
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a listing published notification.
        
        Args:
            listing_id: ID of the listing
            title: Listing title
            price: Listing price
            category: Listing category
            url: Listing URL
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Create message
        message = (
            f"Your listing has been published: {title}\n"
            f"Price: ${price:.2f}\n"
            f"Category: {category}\n"
            f"View your listing at: {url}"
        )
        
        # Create data dictionary
        data = {
            'listing_id': listing_id,
            'title': title,
            'price': price,
            'category': category,
            'url': url,
            'action_url': url
        }
        
        super().__init__(
            notification_type=NotificationType.LISTING_PUBLISHED,
            priority=NotificationPriority.MEDIUM,
            title=f"Listing Published: {title}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

class ErrorConditionNotification(BaseNotification):
    """Notification for error conditions."""
    
    def __init__(
        self,
        error_id: str,
        error_type: str,
        error_message: str,
        severity: str,
        context: Dict[str, Any],
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize an error condition notification.
        
        Args:
            error_id: ID of the error
            error_type: Type of error
            error_message: Error message
            severity: Error severity
            context: Error context
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Determine priority based on severity
        if severity == 'critical':
            priority = NotificationPriority.CRITICAL
        elif severity == 'high':
            priority = NotificationPriority.HIGH
        elif severity == 'medium':
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW
        
        # Create message
        message = (
            f"Error occurred: {error_type}\n"
            f"Message: {error_message}\n"
            f"Severity: {severity}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        # Create data dictionary
        data = {
            'error_id': error_id,
            'error_type': error_type,
            'error_message': error_message,
            'severity': severity,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'action_url': f"/errors/{error_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.ERROR_CONDITION,
            priority=priority,
            title=f"Error: {error_type}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

# Market Intelligence Notifications

class PriceDropNotification(BaseNotification):
    """Notification for price drops."""
    
    def __init__(
        self,
        item_id: str,
        title: str,
        old_price: float,
        new_price: float,
        category: str,
        source: str,
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a price drop notification.
        
        Args:
            item_id: ID of the item
            title: Item title
            old_price: Previous price
            new_price: New price
            category: Item category
            source: Price source
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Calculate price change
        price_change = new_price - old_price
        price_change_percentage = (price_change / old_price) * 100 if old_price > 0 else 0
        
        # Determine priority based on price change
        if abs(price_change_percentage) >= 30:
            priority = NotificationPriority.HIGH
        elif abs(price_change_percentage) >= 15:
            priority = NotificationPriority.MEDIUM
        else:
            priority = NotificationPriority.LOW
        
        # Create message
        message = (
            f"Price drop detected: {title}\n"
            f"Previous price: ${old_price:.2f}\n"
            f"New price: ${new_price:.2f}\n"
            f"Change: ${abs(price_change):.2f} ({abs(price_change_percentage):.1f}%)\n"
            f"Category: {category}\n"
            f"Source: {source}"
        )
        
        # Create data dictionary
        data = {
            'item_id': item_id,
            'title': title,
            'old_price': old_price,
            'new_price': new_price,
            'price_change': price_change,
            'price_change_percentage': price_change_percentage,
            'category': category,
            'source': source,
            'action_url': f"/items/{item_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.PRICE_DROP,
            priority=priority,
            title=f"Price Drop: {title}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

class CompetitorListingNotification(BaseNotification):
    """Notification for competitor listings."""
    
    def __init__(
        self,
        competitor_id: str,
        competitor_name: str,
        item_count: int,
        categories: List[str],
        price_range: Dict[str, float],
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a competitor listing notification.
        
        Args:
            competitor_id: ID of the competitor
            competitor_name: Name of the competitor
            item_count: Number of items listed
            categories: Categories of items
            price_range: Price range of items
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Create message
        message = (
            f"New competitor listings detected: {competitor_name}\n"
            f"Items listed: {item_count}\n"
            f"Categories: {', '.join(categories)}\n"
            f"Price range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}"
        )
        
        # Create data dictionary
        data = {
            'competitor_id': competitor_id,
            'competitor_name': competitor_name,
            'item_count': item_count,
            'categories': categories,
            'price_range': price_range,
            'action_url': f"/competitors/{competitor_id}"
        }
        
        super().__init__(
            notification_type=NotificationType.COMPETITOR_LISTING,
            priority=NotificationPriority.MEDIUM,
            title=f"Competitor Activity: {competitor_name}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        )

class CategoryTrendNotification(BaseNotification):
    """Notification for category trends."""
    
    def __init__(
        self,
        category: str,
        trend_type: str,
        trend_data: Dict[str, Any],
        time_period: str,
        recipient_id: Optional[str] = None,
        delivery_methods: Optional[List[DeliveryMethod]] = None
    ):
        """Initialize a category trend notification.
        
        Args:
            category: Category name
            trend_type: Type of trend
            trend_data: Trend data
            time_period: Time period of the trend
            recipient_id: ID of the recipient
            delivery_methods: List of delivery methods
        """
        # Create message
        if trend_type == 'price_increase':
            message = (
                f"Price increase detected in {category}\n"
                f"Average increase: {trend_data.get('percentage_change', 0):.1f}%\n"
                f"Time period: {time_period}\n"
                f"Items analyzed: {trend_data.get('item_count', 0)}"
            )
        elif trend_type == 'price_decrease':
            message = (
                f"Price decrease detected in {category}\n"
                f"Average decrease: {abs(trend_data.get('percentage_change', 0)):.1f}%\n"
                f"Time period: {time_period}\n"
                f"Items analyzed: {trend_data.get('item_count', 0)}"
            )
        elif trend_type == 'demand_increase':
            message = (
                f"Demand increase detected in {category}\n"
                f"Sales increase: {trend_data.get('percentage_change', 0):.1f}%\n"
                f"Time period: {time_period}\n"
                f"Items analyzed: {trend_data.get('item_count', 0)}"
            )
        elif trend_type == 'demand_decrease':
            message = (
                f"Demand decrease detected in {category}\n"
                f"Sales decrease: {abs(trend_data.get('percentage_change', 0)):.1f}%\n"
                f"Time period: {time_period}\n"
                f"Items analyzed: {trend_data.get('item_count', 0)}"
            )
        else:
            message = (
                f"Trend detected in {category}: {trend_type}\n"
                f"Time period: {time_period}\n"
                f"Items analyzed: {trend_data.get('item_count', 0)}"
            )
        
        # Create data dictionary
        data = {
            'category': category,
            'trend_type': trend_type,
            'trend_data': trend_data,
            'time_period': time_period,
            'action_url': f"/trends/{category}"
        }
        
        super().__init__(
            notification_type=NotificationType.CATEGORY_TREND,
            priority=NotificationPriority.LOW,
            title=f"Category Trend: {category} - {trend_type.replace('_', ' ').title()}",
            message=message,
            data=data,
            delivery_methods=delivery_methods,
            recipient_id=recipient_id
        ) 