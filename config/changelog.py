import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("changelog_manager")

console = Console()

class ChangelogManager:
    """Manages changelog and version migration information."""
    
    def __init__(self, changelog_dir: Optional[str] = None):
        """Initialize the changelog manager.
        
        Args:
            changelog_dir: Path to the changelog directory
        """
        if changelog_dir is None:
            changelog_dir = os.path.expanduser("~/.auction/changelog")
        
        self.changelog_dir = Path(changelog_dir)
        self.changelog_dir.mkdir(parents=True, exist_ok=True)
        
        self.changelog_file = self.changelog_dir / "changelog.json"
        self.migration_file = self.changelog_dir / "migrations.json"
        
        # Initialize changelog if it doesn't exist
        if not self.changelog_file.exists():
            self._initialize_changelog()
        
        # Initialize migration log if it doesn't exist
        if not self.migration_file.exists():
            self._initialize_migration_log()
    
    def _initialize_changelog(self) -> None:
        """Initialize the changelog file."""
        initial_changelog = {
            "versions": [
                {
                    "version": "1.0.0",
                    "date": datetime.now().isoformat(),
                    "changes": {
                        "added": [
                            "Initial release",
                            "Basic auction monitoring",
                            "Product research tools",
                            "Profit calculator",
                            "eBay integration",
                            "Amazon integration",
                            "Google integration"
                        ],
                        "changed": [],
                        "deprecated": [],
                        "removed": [],
                        "fixed": [],
                        "security": []
                    },
                    "breaking_changes": [],
                    "migration_guide": "No migration needed for initial release."
                }
            ]
        }
        
        with open(self.changelog_file, "w") as f:
            json.dump(initial_changelog, f, indent=2)
    
    def _initialize_migration_log(self) -> None:
        """Initialize the migration log file."""
        initial_migration_log = {
            "migrations": []
        }
        
        with open(self.migration_file, "w") as f:
            json.dump(initial_migration_log, f, indent=2)
    
    def add_version(self, version: str, changes: Dict[str, List[str]], breaking_changes: List[str], migration_guide: str) -> None:
        """Add a new version to the changelog.
        
        Args:
            version: Version number
            changes: Dictionary of changes by type
            breaking_changes: List of breaking changes
            migration_guide: Migration guide for the version
        """
        try:
            # Load the changelog
            with open(self.changelog_file, "r") as f:
                changelog = json.load(f)
            
            # Add the new version
            changelog["versions"].insert(0, {
                "version": version,
                "date": datetime.now().isoformat(),
                "changes": changes,
                "breaking_changes": breaking_changes,
                "migration_guide": migration_guide
            })
            
            # Save the changelog
            with open(self.changelog_file, "w") as f:
                json.dump(changelog, f, indent=2)
            
            logger.info(f"Added version {version} to changelog")
        except Exception as e:
            logger.error(f"Failed to add version to changelog: {e}")
    
    def log_migration(self, from_version: str, to_version: str, success: bool, details: Optional[str] = None) -> None:
        """Log a migration attempt.
        
        Args:
            from_version: Source version
            to_version: Target version
            success: Whether the migration was successful
            details: Optional migration details
        """
        try:
            # Load the migration log
            with open(self.migration_file, "r") as f:
                migration_log = json.load(f)
            
            # Add the migration entry
            migration_log["migrations"].append({
                "from_version": from_version,
                "to_version": to_version,
                "date": datetime.now().isoformat(),
                "success": success,
                "details": details
            })
            
            # Save the migration log
            with open(self.migration_file, "w") as f:
                json.dump(migration_log, f, indent=2)
            
            logger.info(f"Logged migration from {from_version} to {to_version}")
        except Exception as e:
            logger.error(f"Failed to log migration: {e}")
    
    def get_version_info(self, version: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific version.
        
        Args:
            version: Version number
            
        Returns:
            Version information if found, None otherwise
        """
        try:
            # Load the changelog
            with open(self.changelog_file, "r") as f:
                changelog = json.load(f)
            
            # Find the version
            for version_info in changelog["versions"]:
                if version_info["version"] == version:
                    return version_info
            
            return None
        except Exception as e:
            logger.error(f"Failed to get version info: {e}")
            return None
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get the migration history.
        
        Returns:
            List of migration entries
        """
        try:
            # Load the migration log
            with open(self.migration_file, "r") as f:
                migration_log = json.load(f)
            
            return migration_log["migrations"]
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []
    
    def show_changelog(self, version: Optional[str] = None) -> None:
        """Show the changelog.
        
        Args:
            version: Optional version to show
        """
        try:
            # Load the changelog
            with open(self.changelog_file, "r") as f:
                changelog = json.load(f)
            
            if version:
                # Show specific version
                version_info = self.get_version_info(version)
                if version_info:
                    self._show_version_info(version_info)
                else:
                    console.print(f"[red]Version {version} not found[/red]")
            else:
                # Show all versions
                for version_info in changelog["versions"]:
                    self._show_version_info(version_info)
                    console.print()
        except Exception as e:
            logger.error(f"Failed to show changelog: {e}")
    
    def _show_version_info(self, version_info: Dict[str, Any]) -> None:
        """Show information about a version.
        
        Args:
            version_info: Version information
        """
        # Create version header
        console.print(f"[bold blue]Version {version_info['version']}[/bold blue]")
        console.print(f"[dim]{version_info['date']}[/dim]")
        console.print()
        
        # Show changes
        if version_info["changes"]:
            table = Table(title="Changes")
            table.add_column("Type", style="cyan")
            table.add_column("Description", style="white")
            
            for change_type, changes in version_info["changes"].items():
                if changes:
                    for change in changes:
                        table.add_row(change_type.title(), change)
            
            console.print(table)
            console.print()
        
        # Show breaking changes
        if version_info["breaking_changes"]:
            console.print("[bold red]Breaking Changes:[/bold red]")
            for change in version_info["breaking_changes"]:
                console.print(f"  • {change}")
            console.print()
        
        # Show migration guide
        if version_info["migration_guide"]:
            console.print("[bold yellow]Migration Guide:[/bold yellow]")
            console.print(version_info["migration_guide"])
            console.print()
    
    def show_migration_history(self) -> None:
        """Show the migration history."""
        try:
            # Get the migration history
            migrations = self.get_migration_history()
            
            if migrations:
                table = Table(title="Migration History")
                table.add_column("From", style="cyan")
                table.add_column("To", style="cyan")
                table.add_column("Date", style="dim")
                table.add_column("Status", style="green")
                table.add_column("Details", style="white")
                
                for migration in migrations:
                    status = "[green]Success[/green]" if migration["success"] else "[red]Failed[/red]"
                    table.add_row(
                        migration["from_version"],
                        migration["to_version"],
                        migration["date"],
                        status,
                        migration.get("details", "")
                    )
                
                console.print(table)
            else:
                console.print("[yellow]No migration history found[/yellow]")
        except Exception as e:
            logger.error(f"Failed to show migration history: {e}")
    
    def get_latest_version(self) -> str:
        """Get the latest version number.
        
        Returns:
            Latest version number
        """
        try:
            # Load the changelog
            with open(self.changelog_file, "r") as f:
                changelog = json.load(f)
            
            # Get the latest version
            return changelog["versions"][0]["version"]
        except Exception as e:
            logger.error(f"Failed to get latest version: {e}")
            return "1.0.0"
    
    def get_breaking_changes(self, from_version: str, to_version: str) -> List[str]:
        """Get breaking changes between versions.
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            List of breaking changes
        """
        try:
            # Load the changelog
            with open(self.changelog_file, "r") as f:
                changelog = json.load(f)
            
            # Find the versions
            from_info = None
            to_info = None
            
            for version_info in changelog["versions"]:
                if version_info["version"] == from_version:
                    from_info = version_info
                elif version_info["version"] == to_version:
                    to_info = version_info
                
                if from_info and to_info:
                    break
            
            if not from_info or not to_info:
                return []
            
            # Get breaking changes
            breaking_changes = []
            
            for version_info in changelog["versions"]:
                version = version_info["version"]
                
                # Check if the version is between from_version and to_version
                if self._is_version_between(version, from_version, to_version):
                    breaking_changes.extend(version_info["breaking_changes"])
            
            return breaking_changes
        except Exception as e:
            logger.error(f"Failed to get breaking changes: {e}")
            return []
    
    def _is_version_between(self, version: str, from_version: str, to_version: str) -> bool:
        """Check if a version is between two versions.
        
        Args:
            version: Version to check
            from_version: Source version
            to_version: Target version
            
        Returns:
            True if the version is between from_version and to_version, False otherwise
        """
        # Split versions into components
        version_parts = [int(x) for x in version.split(".")]
        from_parts = [int(x) for x in from_version.split(".")]
        to_parts = [int(x) for x in to_version.split(".")]
        
        # Compare versions
        return (
            version_parts > from_parts and
            version_parts <= to_parts
        )
    
    def get_migration_guide(self, from_version: str, to_version: str) -> Optional[str]:
        """Get the migration guide between versions.
        
        Args:
            from_version: Source version
            to_version: Target version
            
        Returns:
            Migration guide if found, None otherwise
        """
        try:
            # Load the changelog
            with open(self.changelog_file, "r") as f:
                changelog = json.load(f)
            
            # Find the target version
            for version_info in changelog["versions"]:
                if version_info["version"] == to_version:
                    return version_info["migration_guide"]
            
            return None
        except Exception as e:
            logger.error(f"Failed to get migration guide: {e}")
            return None 