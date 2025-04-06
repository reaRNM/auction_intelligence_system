from typing import List, Optional
import logging
import random
import json
from pathlib import Path
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class UserAgentManager:
    """Service for managing user agent rotation."""
    
    def __init__(self):
        """Initialize the user agent manager."""
        self.user_agents = self._load_user_agents()
        self.current_user_agent = None
        self.last_rotation = 0
        self.rotation_interval = 300  # 5 minutes
    
    def _load_user_agents(self) -> List[str]:
        """Load user agents from configuration.
        
        Returns:
            List of user agent strings
        """
        # Try to load from environment variable first
        user_agent_list = os.getenv("USER_AGENTS", "")
        if user_agent_list:
            return [ua.strip() for ua in user_agent_list.split(",")]
        
        # Fall back to configuration file
        config_path = Path(__file__).parent / "config" / "user_agents.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("user_agents", [])
        
        # Fall back to default user agents
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
        ]
    
    def get_user_agent(self) -> Optional[str]:
        """Get a user agent for use.
        
        Returns:
            User agent string or None if no user agents available
        """
        current_time = time.time()
        
        # Check if we need to rotate
        if (self.current_user_agent is None or 
            current_time - self.last_rotation > self.rotation_interval):
            self.rotate_user_agent()
        
        return self.current_user_agent
    
    def rotate_user_agent(self) -> None:
        """Rotate to a new user agent."""
        if self.user_agents:
            self.current_user_agent = random.choice(self.user_agents)
            logger.info("Rotated to new user agent")
            self.last_rotation = time.time()
        else:
            self.current_user_agent = None
            logger.warning("No user agents available")
    
    def get_user_agent_count(self) -> int:
        """Get the count of available user agents.
        
        Returns:
            Number of available user agents
        """
        return len(self.user_agents) 