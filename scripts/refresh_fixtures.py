#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

def sanitize_data(data: Any) -> Any:
    """Sanitize sensitive data while preserving structure."""
    if isinstance(data, str):
        # Replace email addresses
        data = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'user@example.com', data)
        # Replace API keys
        data = re.sub(r'[a-zA-Z0-9]{32,}', 'X' * 32, data)
        # Replace credit card numbers
        data = re.sub(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}', '4111-1111-1111-1111', data)
        return data
    elif isinstance(data, dict):
        return {k: sanitize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data

def update_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
    """Update timestamps to be relative to current time."""
    now = datetime.now()
    if 'timestamp' in data:
        data['timestamp'] = (now - timedelta(days=1)).isoformat()
    if 'created_at' in data:
        data['created_at'] = (now - timedelta(days=2)).isoformat()
    if 'updated_at' in data:
        data['updated_at'] = now.isoformat()
    return data

def process_fixture_file(file_path: Path) -> None:
    """Process a single fixture file."""
    print(f"Processing {file_path}")
    
    # Read the fixture file
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Sanitize and update the data
    sanitized_data = sanitize_data(data)
    updated_data = update_timestamps(sanitized_data)
    
    # Write back to the file
    with open(file_path, 'w') as f:
        json.dump(updated_data, f, indent=2)

def main():
    """Main function to refresh all test fixtures."""
    fixtures_dir = Path('tests/fixtures')
    
    # Process all JSON files in the fixtures directory
    for fixture_file in fixtures_dir.glob('**/*.json'):
        process_fixture_file(fixture_file)
    
    print("Fixture refresh complete!")

if __name__ == '__main__':
    main() 