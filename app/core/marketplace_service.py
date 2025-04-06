from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta
import logging

from src.services.marketplaces.marketplace_factory import MarketplaceFactory

logger = logging.getLogger(__name__)

class MarketplaceService:
    """Service class for managing marketplace operations."""
    
    def __init__(self):
        """Initialize the marketplace service."""
        self.marketplaces = {}
        self._init_marketplaces()
    
    def _init_marketplaces(self):
        """Initialize marketplace instances."""
        # Get enabled marketplaces from environment
        enabled_marketplaces = os.getenv("ENABLED_MARKETPLACES", "ebay,amazon,local").split(",")
        
        # Initialize each marketplace
        for marketplace_type in enabled_marketplaces:
            try:
                self.marketplaces[marketplace_type] = MarketplaceFactory.get_marketplace(
                    marketplace_type,
                    db_path=os.path.join(os.getenv("DATA_DIR", "data"), f"{marketplace_type}_marketplace.db")
                )
                logger.info(f"Initialized {marketplace_type} marketplace")
            except Exception as e:
                logger.error(f"Failed to initialize {marketplace_type} marketplace: {str(e)}")
    
    def get_listing_analytics(self, marketplace_type: str, listing_id: str) -> Dict:
        """
        Get analytics data for a listing.
        
        Args:
            marketplace_type: Type of marketplace
            listing_id: ID of the listing
            
        Returns:
            Analytics data
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].get_listing_analytics(listing_id)
    
    def update_listing(self, marketplace_type: str, listing_id: str, data: Dict) -> Dict:
        """
        Update a listing.
        
        Args:
            marketplace_type: Type of marketplace
            listing_id: ID of the listing
            data: New listing data
            
        Returns:
            Updated listing data
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].update_listing(listing_id, data)
    
    def create_listing(self, marketplace_type: str, data: Dict) -> Dict:
        """
        Create a new listing.
        
        Args:
            marketplace_type: Type of marketplace
            data: Listing data
            
        Returns:
            Created listing data
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].create_listing(data)
    
    def delete_listing(self, marketplace_type: str, listing_id: str) -> bool:
        """
        Delete a listing.
        
        Args:
            marketplace_type: Type of marketplace
            listing_id: ID of the listing
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].delete_listing(listing_id)
    
    def get_listing_details(self, marketplace_type: str, listing_id: str) -> Dict:
        """
        Get detailed information about a listing.
        
        Args:
            marketplace_type: Type of marketplace
            listing_id: ID of the listing
            
        Returns:
            Listing details
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].get_listing_details(listing_id)
    
    def search_listings(
        self,
        marketplace_type: str,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """
        Search for listings.
        
        Args:
            marketplace_type: Type of marketplace
            query: Search query
            filters: Optional search filters
            page: Page number
            page_size: Number of results per page
            
        Returns:
            Search results
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].search_listings(
            query,
            filters,
            page,
            page_size
        )
    
    def get_market_data(
        self,
        marketplace_type: str,
        category: str,
        filters: Optional[Dict] = None,
        time_range: Optional[str] = None
    ) -> Dict:
        """
        Get market data for a category.
        
        Args:
            marketplace_type: Type of marketplace
            category: Category name
            filters: Optional filters
            time_range: Optional time range ('7d', '30d', '90d')
            
        Returns:
            Market data
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        if marketplace_type not in self.marketplaces:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        return self.marketplaces[marketplace_type].get_market_data(
            category,
            filters,
            time_range
        )
    
    def get_aggregated_market_data(
        self,
        category: str,
        filters: Optional[Dict] = None,
        time_range: Optional[str] = None
    ) -> Dict:
        """
        Get aggregated market data from all marketplaces.
        
        Args:
            category: Category name
            filters: Optional filters
            time_range: Optional time range ('7d', '30d', '90d')
            
        Returns:
            Aggregated market data
        """
        # Get market data from each marketplace
        marketplace_data = {}
        for marketplace_type, marketplace in self.marketplaces.items():
            try:
                marketplace_data[marketplace_type] = marketplace.get_market_data(
                    category,
                    filters,
                    time_range
                )
            except Exception as e:
                logger.error(f"Failed to get market data from {marketplace_type}: {str(e)}")
        
        # Aggregate data
        total_listings = sum(
            data["total_listings"]
            for data in marketplace_data.values()
        )
        
        if total_listings > 0:
            # Calculate weighted average price
            total_value = sum(
                data["average_price"] * data["total_listings"]
                for data in marketplace_data.values()
            )
            average_price = total_value / total_listings
            
            # Get overall price range
            min_price = min(
                data["price_range"]["min"]
                for data in marketplace_data.values()
                if data["price_range"]["min"] > 0
            )
            max_price = max(
                data["price_range"]["max"]
                for data in marketplace_data.values()
            )
            
            # Combine popular filters
            popular_filters = {}
            for data in marketplace_data.values():
                for filter_data in data["popular_filters"]:
                    filter_name = filter_data["name"]
                    if filter_name not in popular_filters:
                        popular_filters[filter_name] = {}
                    
                    for value, count in filter_data["values"].items():
                        popular_filters[filter_name][value] = (
                            popular_filters[filter_name].get(value, 0) + count
                        )
            
            # Calculate overall trends
            all_prices = []
            all_counts = []
            for data in marketplace_data.values():
                for day_data in data["trends"]["daily"].values():
                    all_prices.extend([day_data["average_price"]] * day_data["count"])
                    all_counts.append(day_data["count"])
            
            if all_prices:
                price_trend = "up" if all_prices[-1] > all_prices[0] else "down"
                price_change_percent = (
                    (all_prices[-1] - all_prices[0]) / all_prices[0] * 100
                )
                volume_trend = "up" if all_counts[-1] > all_counts[0] else "down"
                volume_change_percent = (
                    (all_counts[-1] - all_counts[0]) / all_counts[0] * 100
                )
            else:
                price_trend = "neutral"
                price_change_percent = 0.0
                volume_trend = "neutral"
                volume_change_percent = 0.0
            
            return {
                "category": category,
                "total_listings": total_listings,
                "average_price": average_price,
                "price_range": {
                    "min": min_price,
                    "max": max_price
                },
                "popular_filters": [
                    {"name": name, "values": values}
                    for name, values in popular_filters.items()
                ],
                "trends": {
                    "overall": {
                        "price_trend": price_trend,
                        "price_change_percent": price_change_percent,
                        "volume_trend": volume_trend,
                        "volume_change_percent": volume_change_percent
                    }
                },
                "marketplace_data": marketplace_data
            }
        else:
            return {
                "category": category,
                "total_listings": 0,
                "average_price": 0.0,
                "price_range": {
                    "min": 0.0,
                    "max": 0.0
                },
                "popular_filters": [],
                "trends": {
                    "overall": {
                        "price_trend": "neutral",
                        "price_change_percent": 0.0,
                        "volume_trend": "neutral",
                        "volume_change_percent": 0.0
                    }
                },
                "marketplace_data": marketplace_data
            } 