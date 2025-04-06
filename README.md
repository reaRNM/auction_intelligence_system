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
