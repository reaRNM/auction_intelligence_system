import os
import json
import logging
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List
import warnings
from rich.console import Console
from rich.prompt import Confirm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("config_manager")

console = Console()

class ConfigManager:
    """Manages configuration for the Auction Intelligence system."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Path to the configuration directory
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.auction")
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.legacy_config_file = self.config_dir / "config.ini"
        
        # Default configuration
        self.default_config = {
            "version": "1.0.0",
            "api": {
                "ebay": {
                    "app_id": "",
                    "cert_id": "",
                    "dev_id": "",
                    "auth_token": ""
                },
                "amazon": {
                    "access_key": "",
                    "secret_key": "",
                    "associate_tag": ""
                },
                "google": {
                    "api_key": ""
                }
            },
            "preferences": {
                "output_format": "json",
                "notifications": True,
                "auto_bid": False,
                "max_bid_amount": 100.0
            },
            "display": {
                "dark_mode": False,
                "currency": "USD",
                "date_format": "%Y-%m-%d %H:%M:%S"
            },
            "history": {
                "max_entries": 1000,
                "save_to_file": True
            }
        }
        
        # Load the configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load the configuration from the config file.
        
        Returns:
            The configuration dictionary
        """
        # Check if the config file exists
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                
                # Check if the config is a legacy config
                if self._is_legacy_config(config):
                    logger.warning("Legacy configuration detected")
                    config = self._convert_legacy_config(config)
                
                # Check if the config needs to be updated
                if self._needs_update(config):
                    logger.warning("Configuration needs to be updated")
                    config = self._update_config(config)
                
                return config
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                return self.default_config.copy()
        else:
            # Check if the legacy config file exists
            if self.legacy_config_file.exists():
                logger.warning("Legacy configuration file detected")
                config = self._load_legacy_config()
                
                # Convert the legacy config to the new format
                config = self._convert_legacy_config(config)
                
                # Save the new config
                self._save_config(config)
                
                return config
            else:
                # Create a new config file with default values
                self._save_config(self.default_config.copy())
                return self.default_config.copy()
    
    def _is_legacy_config(self, config: Dict[str, Any]) -> bool:
        """Check if the configuration is a legacy configuration.
        
        Args:
            config: The configuration dictionary
            
        Returns:
            True if the configuration is a legacy configuration, False otherwise
        """
        # Check if the config has a version
        if "version" not in config:
            return True
        
        # Check if the config has the expected structure
        if "api" not in config or "preferences" not in config:
            return True
        
        return False
    
    def _load_legacy_config(self) -> Dict[str, Any]:
        """Load the legacy configuration from the legacy config file.
        
        Returns:
            The legacy configuration dictionary
        """
        config = configparser.ConfigParser()
        config.read(self.legacy_config_file)
        
        # Convert the config to a dictionary
        legacy_config = {}
        
        for section in config.sections():
            legacy_config[section] = {}
            for key, value in config[section].items():
                legacy_config[section][key] = value
        
        return legacy_config
    
    def _convert_legacy_config(self, legacy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a legacy configuration to the new format.
        
        Args:
            legacy_config: The legacy configuration dictionary
            
        Returns:
            The new configuration dictionary
        """
        # Create a new config with default values
        new_config = self.default_config.copy()
        
        # Convert the legacy config to the new format
        if "ebay" in legacy_config:
            new_config["api"]["ebay"] = {
                "app_id": legacy_config["ebay"].get("app_id", ""),
                "cert_id": legacy_config["ebay"].get("cert_id", ""),
                "dev_id": legacy_config["ebay"].get("dev_id", ""),
                "auth_token": legacy_config["ebay"].get("auth_token", "")
            }
        
        if "amazon" in legacy_config:
            new_config["api"]["amazon"] = {
                "access_key": legacy_config["amazon"].get("access_key", ""),
                "secret_key": legacy_config["amazon"].get("secret_key", ""),
                "associate_tag": legacy_config["amazon"].get("associate_tag", "")
            }
        
        if "google" in legacy_config:
            new_config["api"]["google"] = {
                "api_key": legacy_config["google"].get("api_key", "")
            }
        
        if "preferences" in legacy_config:
            new_config["preferences"] = {
                "output_format": legacy_config["preferences"].get("output_format", "json"),
                "notifications": legacy_config["preferences"].get("notifications", "true").lower() == "true",
                "auto_bid": legacy_config["preferences"].get("auto_bid", "false").lower() == "true",
                "max_bid_amount": float(legacy_config["preferences"].get("max_bid_amount", "100.0"))
            }
        
        if "display" in legacy_config:
            new_config["display"] = {
                "dark_mode": legacy_config["display"].get("dark_mode", "false").lower() == "true",
                "currency": legacy_config["display"].get("currency", "USD"),
                "date_format": legacy_config["display"].get("date_format", "%Y-%m-%d %H:%M:%S")
            }
        
        if "history" in legacy_config:
            new_config["history"] = {
                "max_entries": int(legacy_config["history"].get("max_entries", "1000")),
                "save_to_file": legacy_config["history"].get("save_to_file", "true").lower() == "true"
            }
        
        # Set the version
        new_config["version"] = "1.0.0"
        
        return new_config
    
    def _needs_update(self, config: Dict[str, Any]) -> bool:
        """Check if the configuration needs to be updated.
        
        Args:
            config: The configuration dictionary
            
        Returns:
            True if the configuration needs to be updated, False otherwise
        """
        # Check if the config has a version
        if "version" not in config:
            return True
        
        # Check if the config has the expected structure
        if "api" not in config or "preferences" not in config:
            return True
        
        # Check if the config has all the expected keys
        for key in self.default_config:
            if key not in config:
                return True
        
        return False
    
    def _update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update the configuration to the latest version.
        
        Args:
            config: The configuration dictionary
            
        Returns:
            The updated configuration dictionary
        """
        # Create a new config with default values
        new_config = self.default_config.copy()
        
        # Update the config with the values from the old config
        for key, value in config.items():
            if key in new_config:
                if isinstance(value, dict) and isinstance(new_config[key], dict):
                    for subkey, subvalue in value.items():
                        if subkey in new_config[key]:
                            new_config[key][subkey] = subvalue
                else:
                    new_config[key] = value
        
        # Set the version
        new_config["version"] = "1.0.0"
        
        return new_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save the configuration to the config file.
        
        Args:
            config: The configuration dictionary
        """
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: The configuration key (dot notation for nested keys)
            default: The default value if the key is not found
            
        Returns:
            The configuration value
        """
        try:
            # Split the key by dots
            keys = key.split(".")
            
            # Get the value
            value = self.config
            for k in keys:
                value = value[k]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: The configuration key (dot notation for nested keys)
            value: The configuration value
        """
        try:
            # Split the key by dots
            keys = key.split(".")
            
            # Get the config
            config = self.config
            
            # Navigate to the nested key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # Set the value
            config[keys[-1]] = value
            
            # Save the config
            self._save_config(self.config)
        except Exception as e:
            logger.error(f"Failed to set configuration value: {e}")
    
    def get_api_key(self, api: str, key: str) -> str:
        """Get an API key.
        
        Args:
            api: The API name (e.g., "ebay", "amazon", "google")
            key: The key name (e.g., "app_id", "access_key", "api_key")
            
        Returns:
            The API key
        """
        return self.get(f"api.{api}.{key}", "")
    
    def set_api_key(self, api: str, key: str, value: str) -> None:
        """Set an API key.
        
        Args:
            api: The API name (e.g., "ebay", "amazon", "google")
            key: The key name (e.g., "app_id", "access_key", "api_key")
            value: The API key value
        """
        self.set(f"api.{api}.{key}", value)
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value.
        
        Args:
            key: The preference key
            default: The default value if the key is not found
            
        Returns:
            The preference value
        """
        return self.get(f"preferences.{key}", default)
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set a preference value.
        
        Args:
            key: The preference key
            value: The preference value
        """
        self.set(f"preferences.{key}", value)
    
    def get_display_setting(self, key: str, default: Any = None) -> Any:
        """Get a display setting value.
        
        Args:
            key: The display setting key
            default: The default value if the key is not found
            
        Returns:
            The display setting value
        """
        return self.get(f"display.{key}", default)
    
    def set_display_setting(self, key: str, value: Any) -> None:
        """Set a display setting value.
        
        Args:
            key: The display setting key
            value: The display setting value
        """
        self.set(f"display.{key}", value)
    
    def get_history_setting(self, key: str, default: Any = None) -> Any:
        """Get a history setting value.
        
        Args:
            key: The history setting key
            default: The default value if the key is not found
            
        Returns:
            The history setting value
        """
        return self.get(f"history.{key}", default)
    
    def set_history_setting(self, key: str, value: Any) -> None:
        """Set a history setting value.
        
        Args:
            key: The history setting key
            value: The history setting value
        """
        self.set(f"history.{key}", value)
    
    def show_deprecation_warning(self, key: str, message: str) -> None:
        """Show a deprecation warning for a configuration key.
        
        Args:
            key: The configuration key
            message: The deprecation message
        """
        warnings.warn(f"Configuration key '{key}' is deprecated: {message}", DeprecationWarning)
    
    def migrate_config(self) -> None:
        """Migrate the configuration to the latest version."""
        # Check if the config needs to be updated
        if self._needs_update(self.config):
            logger.warning("Configuration needs to be updated")
            
            # Ask if the user wants to update the config
            if Confirm.ask("Do you want to update the configuration?"):
                # Update the config
                self.config = self._update_config(self.config)
                
                # Save the config
                self._save_config(self.config)
                
                logger.info("Configuration updated successfully")
            else:
                logger.warning("Configuration update skipped")
        else:
            logger.info("Configuration is up to date")
    
    def backup_config(self) -> None:
        """Backup the configuration."""
        try:
            # Create a backup file
            backup_file = self.config_dir / f"config_{self.config['version']}_backup.json"
            
            # Save the config to the backup file
            with open(backup_file, "w") as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration backed up to {backup_file}")
        except Exception as e:
            logger.error(f"Failed to backup configuration: {e}")
    
    def restore_config(self, backup_file: str) -> None:
        """Restore the configuration from a backup file.
        
        Args:
            backup_file: Path to the backup file
        """
        try:
            # Load the backup file
            with open(backup_file, "r") as f:
                backup_config = json.load(f)
            
            # Ask if the user wants to restore the config
            if Confirm.ask(f"Do you want to restore the configuration from {backup_file}?"):
                # Restore the config
                self.config = backup_config
                
                # Save the config
                self._save_config(self.config)
                
                logger.info("Configuration restored successfully")
            else:
                logger.warning("Configuration restore skipped")
        except Exception as e:
            logger.error(f"Failed to restore configuration: {e}")
    
    def list_backups(self) -> List[str]:
        """List the available backup files.
        
        Returns:
            A list of backup file paths
        """
        try:
            # Get the list of backup files
            backup_files = list(self.config_dir.glob("config_*_backup.json"))
            
            # Return the backup file paths
            return [str(backup_file) for backup_file in backup_files]
        except Exception as e:
            logger.error(f"Failed to list backup files: {e}")
            return []
    
    def show_config(self) -> None:
        """Show the current configuration."""
        # Create a table
        table = Table(title="Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        # Add the config to the table
        self._add_config_to_table(table, self.config)
        
        # Print the table
        console.print(table)
    
    def _add_config_to_table(self, table: Any, config: Dict[str, Any], prefix: str = "") -> None:
        """Add the configuration to a table.
        
        Args:
            table: The table
            config: The configuration dictionary
            prefix: The prefix for the keys
        """
        for key, value in config.items():
            if isinstance(value, dict):
                self._add_config_to_table(table, value, f"{prefix}{key}.")
            else:
                table.add_row(f"{prefix}{key}", str(value))
    
    def reset_config(self) -> None:
        """Reset the configuration to the default values."""
        # Ask if the user wants to reset the config
        if Confirm.ask("Do you want to reset the configuration to the default values?"):
            # Reset the config
            self.config = self.default_config.copy()
            
            # Save the config
            self._save_config(self.config)
            
            logger.info("Configuration reset successfully")
        else:
            logger.warning("Configuration reset skipped") 