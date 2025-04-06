from typing import Dict, List, Optional
import logging
import random
import requests
import time
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ProxyManager:
    """Service for managing proxy rotation."""
    
    def __init__(self):
        """Initialize the proxy manager."""
        self.static_proxies = self._load_static_proxies()
        self.tor_proxies = self._load_tor_proxies()
        self.current_proxy = None
        self.proxy_type = None  # 'static', 'tor', or None
        self.last_rotation = 0
        self.rotation_interval = 300  # 5 minutes
    
    def _load_static_proxies(self) -> List[Dict[str, str]]:
        """Load static residential proxies from configuration.
        
        Returns:
            List of proxy dictionaries
        """
        # Try to load from environment variable first
        proxy_list = os.getenv("STATIC_PROXIES", "")
        if proxy_list:
            return [{"http": proxy.strip(), "https": proxy.strip()} for proxy in proxy_list.split(",")]
        
        # Fall back to configuration file
        config_path = Path(__file__).parent / "config" / "proxies.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("static_proxies", [])
        
        return []
    
    def _load_tor_proxies(self) -> List[Dict[str, str]]:
        """Load Tor network proxies.
        
        Returns:
            List of proxy dictionaries
        """
        # Default Tor SOCKS proxy
        return [{"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}]
    
    def get_proxy(self) -> Optional[Dict[str, str]]:
        """Get a proxy for use.
        
        Returns:
            Proxy dictionary or None if no proxies available
        """
        current_time = time.time()
        
        # Check if we need to rotate
        if (self.current_proxy is None or 
            current_time - self.last_rotation > self.rotation_interval):
            self.rotate_proxy()
        
        return self.current_proxy
    
    def rotate_proxy(self) -> None:
        """Rotate to a new proxy."""
        # Try static proxies first
        if self.static_proxies:
            self.current_proxy = random.choice(self.static_proxies)
            self.proxy_type = "static"
            logger.info("Rotated to static proxy")
            self.last_rotation = time.time()
            return
        
        # Fall back to Tor
        if self.tor_proxies:
            self.current_proxy = random.choice(self.tor_proxies)
            self.proxy_type = "tor"
            logger.info("Rotated to Tor proxy")
            self.last_rotation = time.time()
            return
        
        # No proxies available
        self.current_proxy = None
        self.proxy_type = None
        logger.warning("No proxies available")
    
    def test_proxy(self, proxy: Dict[str, str]) -> bool:
        """Test if a proxy is working.
        
        Args:
            proxy: Proxy dictionary to test
            
        Returns:
            True if proxy is working, False otherwise
        """
        try:
            response = requests.get(
                "https://api.ipify.org?format=json",
                proxies=proxy,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Proxy test failed: {e}")
            return False
    
    def get_proxy_type(self) -> Optional[str]:
        """Get the current proxy type.
        
        Returns:
            Current proxy type or None if no proxy in use
        """
        return self.proxy_type
    
    def get_proxy_count(self) -> Dict[str, int]:
        """Get the count of available proxies by type.
        
        Returns:
            Dictionary of proxy counts by type
        """
        return {
            "static": len(self.static_proxies),
            "tor": len(self.tor_proxies)
        } 