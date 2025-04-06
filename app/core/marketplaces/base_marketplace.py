from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime

class BaseMarketplace(ABC):
    """Base class for marketplace services."""
    
    def __init__(self):
        """Initialize the marketplace service."""
        self.name = self.__class__.__name__.lower().replace("marketplace", "")
    
    @abstractmethod
    def get_listing_analytics(self, listing_id: str) -> Dict:
        """Get analytics data for a specific listing.
        
        Args:
            listing_id: The platform-specific listing ID.
        
        Returns:
            Dictionary containing analytics data:
            {
                "views": int,  # Number of views
                "clicks": int,  # Number of clicks
                "impressions": int,  # Number of impressions
                "conversion_rate": float,  # Conversion rate
                "average_position": float,  # Average search position
                "cost_per_click": float,  # Cost per click
                "total_cost": float,  # Total advertising cost
                "revenue": float,  # Total revenue
                "raw_data": Dict,  # Additional raw data
            }
        """
        pass
    
    @abstractmethod
    def update_listing(self, listing_id: str, data: Dict) -> Dict:
        """Update a listing with new data.
        
        Args:
            listing_id: The platform-specific listing ID.
            data: Dictionary containing update data.
        
        Returns:
            Dictionary containing the updated listing data.
        """
        pass
    
    @abstractmethod
    def create_listing(self, data: Dict) -> Dict:
        """Create a new listing.
        
        Args:
            data: Dictionary containing listing data.
        
        Returns:
            Dictionary containing the created listing data.
        """
        pass
    
    @abstractmethod
    def delete_listing(self, listing_id: str) -> bool:
        """Delete a listing.
        
        Args:
            listing_id: The platform-specific listing ID.
        
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_listing_details(self, listing_id: str) -> Dict:
        """Get detailed information about a listing.
        
        Args:
            listing_id: The platform-specific listing ID.
        
        Returns:
            Dictionary containing listing details.
        """
        pass
    
    @abstractmethod
    def search_listings(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Search for listings matching the query.
        
        Args:
            query: Search query string.
            filters: Optional dictionary of filters to apply.
            page: Page number for pagination.
            page_size: Number of results per page.
        
        Returns:
            Dictionary containing search results:
            {
                "total": int,  # Total number of results
                "page": int,  # Current page number
                "page_size": int,  # Results per page
                "results": List[Dict],  # List of matching listings
            }
        """
        pass
    
    @abstractmethod
    def get_market_data(
        self,
        category: str,
        filters: Optional[Dict] = None,
        time_range: Optional[str] = None
    ) -> Dict:
        """Get market data for a specific category.
        
        Args:
            category: Product category.
            filters: Optional dictionary of filters to apply.
            time_range: Optional time range for the data.
        
        Returns:
            Dictionary containing market data:
            {
                "category": str,  # Product category
                "total_listings": int,  # Total number of listings
                "average_price": float,  # Average listing price
                "price_range": Dict,  # Price range statistics
                "popular_filters": List[Dict],  # Popular filter values
                "trends": Dict,  # Market trends data
                "raw_data": Dict,  # Additional raw data
            }
        """
        pass
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        """Format a timestamp for the marketplace API.
        
        Args:
            timestamp: Datetime object to format.
        
        Returns:
            Formatted timestamp string.
        """
        return timestamp.isoformat()
    
    def _parse_timestamp(self, timestamp: str) -> datetime:
        """Parse a timestamp from the marketplace API.
        
        Args:
            timestamp: Timestamp string to parse.
        
        Returns:
            Datetime object.
        """
        return datetime.fromisoformat(timestamp)
    
    def _validate_listing_data(self, data: Dict) -> bool:
        """Validate listing data before submission.
        
        Args:
            data: Dictionary containing listing data.
        
        Returns:
            True if valid, False otherwise.
        """
        required_fields = ["title", "description", "price", "category"]
        return all(field in data for field in required_fields)
    
    def _format_listing_data(self, data: Dict) -> Dict:
        """Format listing data for the marketplace API.
        
        Args:
            data: Dictionary containing listing data.
        
        Returns:
            Formatted listing data dictionary.
        """
        return {
            "title": data["title"],
            "description": data["description"],
            "price": float(data["price"]),
            "category": data["category"],
            "condition": data.get("condition", "new"),
            "quantity": int(data.get("quantity", 1)),
            "images": data.get("images", []),
            "attributes": data.get("attributes", {}),
            "shipping": data.get("shipping", {}),
            "metadata": data.get("metadata", {}),
        } 