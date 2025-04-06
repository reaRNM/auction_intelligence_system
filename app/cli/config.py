import os
from pathlib import Path
import configparser
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for the Auction Intelligence CLI."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".auction"
        self.config_file = self.config_dir / "config.ini"
        self.config = self._load_config()
    
    def _load_config(self) -> configparser.ConfigParser:
        """Load configuration from file or create default if not exists."""
        config = configparser.ConfigParser()
        
        if not self.config_file.exists():
            self._create_default_config(config)
        else:
            config.read(self.config_file)
        
        return config
    
    def _create_default_config(self, config: configparser.ConfigParser):
        """Create default configuration file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        config["API"] = {
            "ebay_api_key": "",
            "amazon_api_key": "",
            "google_api_key": ""
        }
        
        config["Preferences"] = {
            "default_format": "json",
            "notifications_enabled": "true",
            "debug_mode": "false"
        }
        
        config["Display"] = {
            "color_output": "true",
            "progress_bars": "true",
            "table_style": "default"
        }
        
        config["History"] = {
            "max_history": "1000",
            "save_history": "true"
        }
        
        with open(self.config_file, "w") as f:
            config.write(f)
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set(self, section: str, key: str, value: str):
        """Set a configuration value."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        self._save_config()
    
    def _save_config(self):
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            self.config.write(f)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service."""
        return self.get("API", f"{service}_api_key")
    
    def set_api_key(self, service: str, key: str):
        """Set API key for a specific service."""
        self.set("API", f"{service}_api_key", key)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        return self.get("Preferences", key, default)
    
    def set_preference(self, key: str, value: str):
        """Set a preference value."""
        self.set("Preferences", key, value)
    
    def get_display_setting(self, key: str, default: Any = None) -> Any:
        """Get a display setting value."""
        return self.get("Display", key, default)
    
    def set_display_setting(self, key: str, value: str):
        """Set a display setting value."""
        self.set("Display", key, value)
    
    def get_history_setting(self, key: str, default: Any = None) -> Any:
        """Get a history setting value."""
        return self.get("History", key, default)
    
    def set_history_setting(self, key: str, value: str):
        """Set a history setting value."""
        self.set("History", key, value)
    
    def validate(self) -> Dict[str, str]:
        """Validate configuration and return any errors."""
        errors = {}
        
        # Check required API keys
        required_apis = ["ebay", "amazon", "google"]
        for api in required_apis:
            if not self.get_api_key(api):
                errors[f"api_{api}"] = f"Missing {api.title()} API key"
        
        # Validate preferences
        if self.get_preference("default_format") not in ["json", "csv"]:
            errors["format"] = "Invalid default format"
        
        # Validate display settings
        if self.get_display_setting("color_output") not in ["true", "false"]:
            errors["color"] = "Invalid color output setting"
        
        return errors 