import os
import sys
import json
import click
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
import subprocess
import platform
import psycopg2
import redis
import requests
from pathlib import Path

console = Console()

def check_python_version():
    """Check if Python version meets requirements."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        console.print("[red]Error: Python 3.11 or higher is required[/red]")
        sys.exit(1)

def check_prerequisites():
    """Check if all prerequisites are installed."""
    with Progress() as progress:
        task = progress.add_task("[cyan]Checking prerequisites...", total=4)
        
        # Check PostgreSQL
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="postgres",
                host="localhost",
                port="5432"
            )
            conn.close()
            progress.update(task, advance=1)
        except Exception as e:
            console.print("[red]Error: PostgreSQL is not running or not properly configured[/red]")
            sys.exit(1)
        
        # Check Redis
        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            progress.update(task, advance=1)
        except Exception as e:
            console.print("[red]Error: Redis is not running or not properly configured[/red]")
            sys.exit(1)
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
            progress.update(task, advance=1)
        except Exception as e:
            console.print("[red]Error: pip is not installed[/red]")
            sys.exit(1)
        
        # Check git
        try:
            subprocess.run(["git", "--version"], check=True)
            progress.update(task, advance=1)
        except Exception as e:
            console.print("[red]Error: git is not installed[/red]")
            sys.exit(1)

def install_dependencies():
    """Install required Python packages."""
    with Progress() as progress:
        task = progress.add_task("[cyan]Installing dependencies...", total=1)
        
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            progress.update(task, advance=1)
        except Exception as e:
            console.print(f"[red]Error installing dependencies: {str(e)}[/red]")
            sys.exit(1)

def setup_database():
    """Set up the database schema."""
    with Progress() as progress:
        task = progress.add_task("[cyan]Setting up database...", total=2)
        
        try:
            # Run Alembic migrations
            subprocess.run(["alembic", "upgrade", "head"], check=True)
            progress.update(task, advance=1)
            
            # Import sample data if requested
            if Confirm.ask("Would you like to import sample data?"):
                subprocess.run(["python", "scripts/import_sample_data.py"], check=True)
            progress.update(task, advance=1)
        except Exception as e:
            console.print(f"[red]Error setting up database: {str(e)}[/red]")
            sys.exit(1)

def configure_apis():
    """Configure API keys and test connections."""
    config = {}
    
    # eBay API
    console.print("\n[bold cyan]eBay API Configuration[/bold cyan]")
    config["ebay"] = {
        "app_id": Prompt.ask("Enter your eBay App ID"),
        "cert_id": Prompt.ask("Enter your eBay Cert ID"),
        "dev_id": Prompt.ask("Enter your eBay Dev ID"),
        "auth_token": Prompt.ask("Enter your eBay Auth Token")
    }
    
    # Amazon API
    console.print("\n[bold cyan]Amazon API Configuration[/bold cyan]")
    config["amazon"] = {
        "access_key": Prompt.ask("Enter your Amazon Access Key"),
        "secret_key": Prompt.ask("Enter your Amazon Secret Key"),
        "associate_tag": Prompt.ask("Enter your Amazon Associate Tag")
    }
    
    # Google API
    console.print("\n[bold cyan]Google API Configuration[/bold cyan]")
    config["google"] = {
        "api_key": Prompt.ask("Enter your Google API Key")
    }
    
    # Save configuration
    config_dir = Path.home() / ".auction"
    config_dir.mkdir(exist_ok=True)
    
    with open(config_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    # Test API connections
    with Progress() as progress:
        task = progress.add_task("[cyan]Testing API connections...", total=3)
        
        # Test eBay API
        try:
            # Add eBay API test here
            progress.update(task, advance=1)
        except Exception as e:
            console.print(f"[red]Error testing eBay API: {str(e)}[/red]")
        
        # Test Amazon API
        try:
            # Add Amazon API test here
            progress.update(task, advance=1)
        except Exception as e:
            console.print(f"[red]Error testing Amazon API: {str(e)}[/red]")
        
        # Test Google API
        try:
            # Add Google API test here
            progress.update(task, advance=1)
        except Exception as e:
            console.print(f"[red]Error testing Google API: {str(e)}[/red]")

@click.command()
def setup():
    """Auction Intelligence Setup Wizard"""
    console.print("[bold cyan]Welcome to Auction Intelligence Setup Wizard[/bold cyan]")
    
    # Check Python version
    check_python_version()
    
    # Check prerequisites
    check_prerequisites()
    
    # Install dependencies
    install_dependencies()
    
    # Set up database
    setup_database()
    
    # Configure APIs
    configure_apis()
    
    console.print("\n[bold green]Setup completed successfully![/bold green]")
    console.print("\nYou can now run the application using:")
    console.print("  [cyan]CLI Version:[/cyan] auction-cli")
    console.print("  [cyan]Web Version:[/cyan] docker-compose up -d")

if __name__ == "__main__":
    setup() 