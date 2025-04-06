import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import alembic.config
import alembic.command
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migration_manager")

console = Console()

class MigrationManager:
    """Manages database migrations using Alembic."""
    
    def __init__(self, alembic_ini_path: str = "alembic.ini"):
        """Initialize the migration manager.
        
        Args:
            alembic_ini_path: Path to the Alembic configuration file
        """
        self.alembic_ini_path = alembic_ini_path
        self.alembic_cfg = alembic.config.Config(alembic_ini_path)
        
        # Ensure migrations directory exists
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            migrations_dir.mkdir(parents=True)
    
    def get_current_revision(self) -> Optional[str]:
        """Get the current database revision.
        
        Returns:
            The current revision ID or None if no migrations have been applied
        """
        try:
            # Run alembic current to get the current revision
            result = subprocess.run(
                ["alembic", "current", "-c", self.alembic_ini_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to get the revision ID
            for line in result.stdout.splitlines():
                if "Current revision" in line:
                    revision = line.split(":")[1].strip()
                    return revision if revision != "None" else None
            
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get current revision: {e}")
            return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get the migration history.
        
        Returns:
            List of dictionaries containing migration information
        """
        try:
            # Run alembic history to get the migration history
            result = subprocess.run(
                ["alembic", "history", "-c", self.alembic_ini_path, "--indicate-current"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the output to get the migration history
            history = []
            current_revision = self.get_current_revision()
            
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("Current"):
                    parts = line.split(" ", 1)
                    if len(parts) >= 2:
                        revision = parts[0]
                        description = parts[1].strip()
                        is_current = revision == current_revision
                        history.append({
                            "revision": revision,
                            "description": description,
                            "is_current": is_current
                        })
            
            return history
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def create_migration(self, message: str) -> bool:
        """Create a new migration.
        
        Args:
            message: Description of the migration
            
        Returns:
            True if the migration was created successfully, False otherwise
        """
        try:
            # Run alembic revision to create a new migration
            subprocess.run(
                ["alembic", "revision", "-c", self.alembic_ini_path, "--autogenerate", "-m", message],
                check=True
            )
            logger.info(f"Created migration: {message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create migration: {e}")
            return False
    
    def upgrade(self, revision: str = "head") -> bool:
        """Upgrade the database to the specified revision.
        
        Args:
            revision: The revision to upgrade to (default: "head")
            
        Returns:
            True if the upgrade was successful, False otherwise
        """
        try:
            # Run alembic upgrade to upgrade the database
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Upgrading database to {revision}...", total=1)
                
                # Run pre-migration validation
                self._run_pre_migration_validation()
                
                # Run the upgrade
                alembic.command.upgrade(self.alembic_cfg, revision)
                
                # Run post-migration validation
                self._run_post_migration_validation()
                
                progress.update(task, advance=1)
            
            logger.info(f"Upgraded database to {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to upgrade database: {e}")
            return False
    
    def downgrade(self, revision: str) -> bool:
        """Downgrade the database to the specified revision.
        
        Args:
            revision: The revision to downgrade to
            
        Returns:
            True if the downgrade was successful, False otherwise
        """
        try:
            # Confirm the downgrade
            if not Confirm.ask(f"Are you sure you want to downgrade to {revision}? This may result in data loss."):
                logger.info("Downgrade cancelled")
                return False
            
            # Run alembic downgrade to downgrade the database
            with Progress() as progress:
                task = progress.add_task(f"[cyan]Downgrading database to {revision}...", total=1)
                
                # Run pre-migration validation
                self._run_pre_migration_validation()
                
                # Run the downgrade
                alembic.command.downgrade(self.alembic_cfg, revision)
                
                # Run post-migration validation
                self._run_post_migration_validation()
                
                progress.update(task, advance=1)
            
            logger.info(f"Downgraded database to {revision}")
            return True
        except Exception as e:
            logger.error(f"Failed to downgrade database: {e}")
            return False
    
    def _run_pre_migration_validation(self) -> None:
        """Run validation before migration."""
        try:
            # Import the validation module
            from auction_intelligence.src.migrations.validation import run_pre_migration_validation
            
            # Run the validation
            run_pre_migration_validation()
        except ImportError:
            logger.warning("Pre-migration validation module not found")
        except Exception as e:
            logger.error(f"Pre-migration validation failed: {e}")
    
    def _run_post_migration_validation(self) -> None:
        """Run validation after migration."""
        try:
            # Import the validation module
            from auction_intelligence.src.migrations.validation import run_post_migration_validation
            
            # Run the validation
            run_post_migration_validation()
        except ImportError:
            logger.warning("Post-migration validation module not found")
        except Exception as e:
            logger.error(f"Post-migration validation failed: {e}")
    
    def check_for_pending_migrations(self) -> bool:
        """Check if there are pending migrations.
        
        Returns:
            True if there are pending migrations, False otherwise
        """
        try:
            # Run alembic heads to get the latest revision
            result = subprocess.run(
                ["alembic", "heads", "-c", self.alembic_ini_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get the current revision
            current_revision = self.get_current_revision()
            
            # Check if there are pending migrations
            if current_revision is None:
                return True
            
            # Parse the output to get the latest revision
            latest_revision = None
            for line in result.stdout.splitlines():
                if line.strip():
                    latest_revision = line.strip()
                    break
            
            return latest_revision != current_revision
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check for pending migrations: {e}")
            return False
    
    def run_migration_check(self) -> None:
        """Run a migration check and upgrade if necessary."""
        if self.check_for_pending_migrations():
            console.print("[yellow]Pending migrations detected[/yellow]")
            
            # Get the migration history
            history = self.get_migration_history()
            
            # Display the migration history
            console.print("\n[bold cyan]Migration History:[/bold cyan]")
            for migration in history:
                if migration["is_current"]:
                    console.print(f"  [green]✓ {migration['revision']} - {migration['description']}[/green]")
                else:
                    console.print(f"  {migration['revision']} - {migration['description']}")
            
            # Ask if the user wants to upgrade
            if Confirm.ask("Do you want to upgrade to the latest revision?"):
                self.upgrade()
            else:
                console.print("[yellow]Migration skipped[/yellow]")
        else:
            console.print("[green]No pending migrations[/green]") 