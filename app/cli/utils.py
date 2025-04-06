import os
import sys
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
import json
import csv
from datetime import datetime

console = Console()

def format_output(data: Dict[str, Any], format: str = "json") -> None:
    """Format and print data in the specified format."""
    if format == "json":
        console.print(Syntax(json.dumps(data, indent=2), "json"))
    elif format == "csv":
        writer = csv.writer(sys.stdout)
        writer.writerow(data.keys())
        writer.writerow(data.values())
    else:
        raise ValueError(f"Unsupported output format: {format}")

def create_progress_bar(description: str) -> Progress:
    """Create a progress bar with spinner."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )

def print_table(
    title: str,
    columns: List[str],
    rows: List[List[str]],
    styles: Optional[Dict[str, str]] = None
) -> None:
    """Print data in a formatted table."""
    table = Table(title=title)
    
    # Add columns with optional styles
    for col in columns:
        style = styles.get(col, "default") if styles else "default"
        table.add_column(col, style=style)
    
    # Add rows
    for row in rows:
        table.add_row(*row)
    
    console.print(table)

def print_panel(
    content: str,
    title: Optional[str] = None,
    border_style: str = "blue"
) -> None:
    """Print content in a panel."""
    console.print(Panel.fit(content, title=title, border_style=border_style))

def prompt_for_input(
    message: str,
    default: Optional[str] = None,
    password: bool = False
) -> str:
    """Prompt user for input with optional default value."""
    return Prompt.ask(
        message,
        default=default,
        password=password
    )

def confirm_action(message: str, default: bool = True) -> bool:
    """Prompt user to confirm an action."""
    return Confirm.ask(message, default=default)

def handle_error(error: Exception, debug: bool = False) -> None:
    """Handle and display errors with optional debug information."""
    if debug:
        console.print_exception()
    else:
        console.print(f"[red]Error:[/red] {str(error)}")
        console.print("\n[yellow]Tip:[/yellow] Use --debug for more information")

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display."""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return timestamp

def format_currency(amount: float) -> str:
    """Format currency amount for display."""
    return f"${amount:,.2f}"

def format_percentage(value: float) -> str:
    """Format percentage value for display."""
    return f"{value:.1f}%"

def format_trend(value: float) -> str:
    """Format trend value with arrow indicator."""
    if value > 0:
        return f"↗️ {format_percentage(value)}"
    elif value < 0:
        return f"↘️ {format_percentage(abs(value))}"
    else:
        return f"→ {format_percentage(value)}"

def validate_api_key(key: str) -> bool:
    """Validate API key format."""
    # Add specific validation rules for different API keys
    return bool(key and len(key) >= 32)

def validate_auction_id(auction_id: str) -> bool:
    """Validate auction ID format."""
    # Add specific validation rules for auction IDs
    return bool(auction_id and auction_id.isalnum())

def validate_category(category: str) -> bool:
    """Validate product category."""
    valid_categories = [
        "electronics",
        "clothing",
        "home",
        "sports",
        "collectibles",
        "other"
    ]
    return category.lower() in valid_categories

def get_terminal_size() -> tuple:
    """Get terminal dimensions."""
    return os.get_terminal_size()

def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

def print_help_text(command: str) -> None:
    """Print help text for a command."""
    help_texts = {
        "scrape": """
Scrape auction data for analysis.

Usage:
  auction-scrape <auction_id> [--output=json|csv]

Options:
  --output    Output format (json or csv)
  --debug     Enable debug mode
""",
        "research-product": """
Research product market value and trends.

Usage:
  research-product "product name" [--fast]

Options:
  --fast      Use fast analysis mode
  --debug     Enable debug mode
""",
        "profit-calc": """
Calculate potential profit for a bid.

Usage:
  profit-calc --bid=<amount> --category=<category>

Options:
  --bid       Bid amount
  --category  Product category
  --debug     Enable debug mode
"""
    }
    
    if command in help_texts:
        console.print(Panel.fit(
            help_texts[command],
            title=f"Help: {command}",
            border_style="green"
        ))
    else:
        console.print(f"[red]Error:[/red] No help available for command: {command}") 