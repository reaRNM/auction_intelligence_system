from typing import Dict, Optional, Type
import logging
from .base_scraper import BaseScraper
from .ebay_scraper import EbayScraper
from ..proxy_manager import ProxyManager
from ..user_agent_manager import UserAgentManager

logger = logging.getLogger(__name__)

class ScraperFactory:
    """Factory class for creating scraper instances."""
    
    _instances: Dict[str, BaseScraper] = {}
    _proxy_manager: Optional[ProxyManager] = None
    _user_agent_manager: Optional[UserAgentManager] = None
    
    @classmethod
    def get_scraper(cls, scraper_type: str) -> BaseScraper:
        """Get a scraper instance.
        
        Args:
            scraper_type: Type of scraper to create
            
        Returns:
            Scraper instance
            
        Raises:
            ValueError: If scraper type is invalid
        """
        # Initialize managers if needed
        if cls._proxy_manager is None:
            cls._proxy_manager = ProxyManager()
        if cls._user_agent_manager is None:
            cls._user_agent_manager = UserAgentManager()
        
        # Return existing instance if available
        if scraper_type in cls._instances:
            return cls._instances[scraper_type]
        
        # Create new instance
        scraper_class = cls._get_scraper_class(scraper_type)
        if scraper_class:
            instance = scraper_class(cls._proxy_manager, cls._user_agent_manager)
            cls._instances[scraper_type] = instance
            return instance
        
        raise ValueError(f"Invalid scraper type: {scraper_type}")
    
    @classmethod
    def _get_scraper_class(cls, scraper_type: str) -> Optional[Type[BaseScraper]]:
        """Get the scraper class for a given type.
        
        Args:
            scraper_type: Type of scraper
            
        Returns:
            Scraper class or None if type is invalid
        """
        scrapers = {
            "ebay": EbayScraper,
            # Add more scrapers here as they are implemented
        }
        return scrapers.get(scraper_type.lower())
    
    @classmethod
    def get_all_scrapers(cls) -> Dict[str, BaseScraper]:
        """Get all scraper instances.
        
        Returns:
            Dictionary of scraper instances
        """
        return cls._instances.copy()
    
    @classmethod
    def clear_instances(cls) -> None:
        """Clear all scraper instances."""
        cls._instances.clear()
    
    @classmethod
    def set_proxy_manager(cls, proxy_manager: ProxyManager) -> None:
        """Set the proxy manager instance.
        
        Args:
            proxy_manager: Proxy manager instance
        """
        cls._proxy_manager = proxy_manager
    
    @classmethod
    def set_user_agent_manager(cls, user_agent_manager: UserAgentManager) -> None:
        """Set the user agent manager instance.
        
        Args:
            user_agent_manager: User agent manager instance
        """
        cls._user_agent_manager = user_agent_manager 