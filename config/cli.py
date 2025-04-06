import click
import json
from typing import Dict, Any
import getpass
import logging
from pathlib import Path

from .manager import ConfigManager
from .schema import UserConfig

logger = logging.getLogger(__name__)

def format_value(value: Any) -> str:
    """Format configuration value for display.
    
    Args:
        value: Value to format
        
    Returns:
        Formatted string
    """
    if isinstance(value, dict):
        return json.dumps(value, indent=2)
    elif isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    return str(value)

@click.group()
def config():
    """Manage user configuration."""
    pass

@config.command()
@click.option('--path', '-p', help='Path to config file')
def init(path: str):
    """Initialize new configuration."""
    try:
        # Get password
        password = getpass.getpass("Enter configuration password: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if password != confirm:
            click.echo("Passwords do not match")
            return
        
        # Initialize config
        manager = ConfigManager(path)
        config = manager.load(password)
        
        # Save empty config
        manager.save(password)
        
        click.echo("Configuration initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        click.echo(f"Error: {e}")

@config.command()
@click.option('--path', '-p', help='Path to config file')
@click.option('--section', '-s', help='Configuration section')
@click.option('--key', '-k', help='Configuration key')
def show(path: str, section: str, key: str):
    """Show configuration values."""
    try:
        # Get password
        password = getpass.getpass("Enter configuration password: ")
        
        # Load config
        manager = ConfigManager(path)
        config = manager.load(password)
        
        # Show values
        if section:
            if key:
                value = manager.get(section, key)
                click.echo(f"{section}.{key}:")
                click.echo(format_value(value))
            else:
                section_config = manager.get(section)
                click.echo(f"{section}:")
                for field, value in section_config.dict().items():
                    click.echo(f"  {field}:")
                    click.echo(f"    {format_value(value)}")
        else:
            click.echo("Current configuration:")
            for section_name in UserConfig.__fields__:
                section_config = manager.get(section_name)
                click.echo(f"\n{section_name}:")
                for field, value in section_config.dict().items():
                    click.echo(f"  {field}:")
                    click.echo(f"    {format_value(value)}")
        
    except Exception as e:
        logger.error(f"Failed to show configuration: {e}")
        click.echo(f"Error: {e}")

@config.command()
@click.option('--path', '-p', help='Path to config file')
@click.option('--section', '-s', required=True, help='Configuration section')
@click.option('--updates', '-u', required=True, help='JSON string of updates')
def update(path: str, section: str, updates: str):
    """Update configuration values."""
    try:
        # Parse updates
        try:
            update_dict = json.loads(updates)
        except json.JSONDecodeError:
            click.echo("Invalid JSON format for updates")
            return
        
        # Get password
        password = getpass.getpass("Enter configuration password: ")
        
        # Update config
        manager = ConfigManager(path)
        manager.load(password)
        manager.update(section, update_dict)
        manager.save(password)
        
        click.echo(f"Updated {section} configuration")
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        click.echo(f"Error: {e}")

@config.command()
@click.option('--path', '-p', help='Path to config file')
def reset(path: str):
    """Reset configuration to defaults."""
    try:
        # Get password
        password = getpass.getpass("Enter configuration password: ")
        
        # Reset config
        manager = ConfigManager(path)
        manager._config = UserConfig()
        manager.save(password)
        
        click.echo("Configuration reset to defaults")
        
    except Exception as e:
        logger.error(f"Failed to reset configuration: {e}")
        click.echo(f"Error: {e}")

if __name__ == '__main__':
    config() 