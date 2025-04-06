from typing import Dict, Optional
import os

from src.services.marketplaces.base_marketplace import BaseMarketplace
from src.services.marketplaces.ebay_marketplace import EbayMarketplace
from src.services.marketplaces.amazon_marketplace import AmazonMarketplace
from src.services.marketplaces.local_marketplace import LocalMarketplace

class MarketplaceFactory:
    """Factory class for creating marketplace service instances."""
    
    _instances: Dict[str, BaseMarketplace] = {}
    
    @classmethod
    def get_marketplace(
        cls,
        marketplace_type: str,
        db_path: Optional[str] = None
    ) -> BaseMarketplace:
        """
        Get a marketplace service instance.
        
        Args:
            marketplace_type: Type of marketplace ('ebay', 'amazon', or 'local')
            db_path: Optional path to local database file (only for local marketplace)
            
        Returns:
            Marketplace service instance
            
        Raises:
            ValueError: If marketplace type is invalid
        """
        # Check if instance already exists
        if marketplace_type in cls._instances:
            return cls._instances[marketplace_type]
        
        # Create new instance
        if marketplace_type == "ebay":
            instance = EbayMarketplace()
        elif marketplace_type == "amazon":
            instance = AmazonMarketplace()
        elif marketplace_type == "local":
            instance = LocalMarketplace(db_path)
        else:
            raise ValueError(f"Invalid marketplace type: {marketplace_type}")
        
        # Store instance
        cls._instances[marketplace_type] = instance
        
        return instance
    
    @classmethod
    def get_all_marketplaces(cls) -> Dict[str, BaseMarketplace]:
        """
        Get all marketplace service instances.
        
        Returns:
            Dictionary of marketplace type to instance
        """
        return cls._instances.copy()
    
    @classmethod
    def clear_instances(cls):
        """Clear all marketplace service instances."""
        cls._instances.clear() 