#!/bin/bash

# Install required system packages
sudo apt-get update
sudo apt-get install -y tree

# Create directory structure
mkdir -p ~/auction_intelligence_system/{app/{core,cli,web},config,data/{auctions,research},docs,tests,venv}

# Create virtual environment
cd ~/auction_intelligence_system
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Move files to new structure
if [ -d ~/auction_intelligence ]; then
    # Move configuration files
    cp -r ~/auction_intelligence/src/config/* ~/auction_intelligence_system/config/ 2>/dev/null || true
    cp ~/auction_intelligence/alembic.ini ~/auction_intelligence_system/config/ 2>/dev/null || true
    
    # Move core modules
    cp -r ~/auction_intelligence/src/migrations/* ~/auction_intelligence_system/app/core/ 2>/dev/null || true
    cp -r ~/auction_intelligence/src/services/* ~/auction_intelligence_system/app/core/ 2>/dev/null || true
    cp -r ~/auction_intelligence/src/db/* ~/auction_intelligence_system/app/core/ 2>/dev/null || true
    cp -r ~/auction_intelligence/src/models/* ~/auction_intelligence_system/app/core/ 2>/dev/null || true
    cp -r ~/auction_intelligence/src/api/* ~/auction_intelligence_system/app/core/ 2>/dev/null || true
    cp ~/auction_intelligence/src/setup.py ~/auction_intelligence_system/app/core/ 2>/dev/null || true
    
    # Move web interface
    cp -r ~/auction_intelligence/src/web/* ~/auction_intelligence_system/app/web/ 2>/dev/null || true
    
    # Move CLI tools
    cp -r ~/auction_intelligence/src/cli/* ~/auction_intelligence_system/app/cli/ 2>/dev/null || true
    
    # Move documentation
    cp ~/auction_intelligence/README.md ~/auction_intelligence_system/docs/ 2>/dev/null || true
    
    # Move root files
    cp ~/auction_intelligence/docker-compose.yml ~/auction_intelligence_system/ 2>/dev/null || true
    cp ~/auction_intelligence/requirements.txt ~/auction_intelligence_system/ 2>/dev/null || true
fi

# Create necessary __init__.py files
touch ~/auction_intelligence_system/app/__init__.py
touch ~/auction_intelligence_system/app/core/__init__.py
touch ~/auction_intelligence_system/app/cli/__init__.py
touch ~/auction_intelligence_system/app/web/__init__.py

# Set permissions
chmod -R 750 ~/auction_intelligence_system
chown -R $USER:$USER ~/auction_intelligence_system
chmod 770 ~/auction_intelligence_system/data/*

# Update paths in configuration files
find ~/auction_intelligence_system/config -type f -name "*.json" -exec sed -i 's|~/auction|~/auction_intelligence_system|g' {} +
find ~/auction_intelligence_system/config -type f -name "*.ini" -exec sed -i 's|~/auction|~/auction_intelligence_system|g' {} +

# Create a basic README if it doesn't exist
if [ ! -f ~/auction_intelligence_system/README.md ]; then
    cat > ~/auction_intelligence_system/README.md << 'EOF'
# Auction Intelligence System

A powerful tool for auction monitoring, product research, and profit calculation.

## Directory Structure

```
auction_intelligence_system/
├── app/                # Main application code
│   ├── core/          # Core modules
│   ├── cli/           # CLI-specific code
│   └── web/           # Web interface code
├── config/            # Configuration files
├── data/              # Database and scraped data
│   ├── auctions/      # Raw auction data
│   └── research/      # Market research data
├── docs/              # Documentation
├── tests/             # Test suites
└── venv/              # Python virtual environment
```

## Setup Instructions

1. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the system:
   ```bash
   python -m app.core.setup
   ```

## Usage

- CLI Version: `python -m app.cli.main`
- Web Version: `streamlit run app/web/app.py`

## Development

- Run tests: `pytest`
- Format code: `black .`
- Check types: `mypy .`
EOF
fi

echo "Setup completed successfully!" 