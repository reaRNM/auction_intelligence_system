# Auction Intelligence System

A self-hosted web application for auction analysis and intelligent listing optimization. The system uses AI-powered analysis to help users identify profitable auction opportunities and create optimized listings.

## Features

- **Auction Scraping**: Automated scraping of auction sites with intelligent rate limiting and proxy rotation
- **Product Research**: Market analysis and price prediction using machine learning models
- **Profit Calculator**: Detailed cost breakdown and profit margin analysis
- **Shipping Estimator**: Multi-carrier shipping cost calculation and optimization
- **Listing Generator**: AI-powered listing creation with SEO optimization
- **Learning Module**: Continuous improvement through machine learning and data analysis

## Architecture

The system is built with a modern microservices architecture:

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: Streamlit
- **Database**: PostgreSQL 15+ with pg_trgm and pgvector extensions
- **Cache**: Redis
- **Task Queue**: Celery with Redis backend
- **Reverse Proxy**: Nginx
- **AI/ML**: GPT-4-turbo, Scikit-learn, and Ray LLM models

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis
- OpenAI API key
- eBay API credentials
- Keepa API key
- Shippo API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/auction_intelligence.git
cd auction_intelligence
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Update the `.env` file with your API keys and configuration settings.

4. Build and start the containers:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost
- API Documentation: http://localhost/api/docs
- Flower Dashboard: http://localhost:5555

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install pre-commit hooks:
```bash
pre-commit install
```

4. Run tests:
```bash
pytest
```

## Project Structure

```
auction_intelligence/
├── src/
│   ├── api/            # FastAPI application
│   ├── models/         # SQLAlchemy models
│   ├── services/       # Business logic
│   ├── utils/          # Utility functions
│   ├── db/             # Database migrations
│   ├── ml/             # Machine learning models
│   ├── scrapers/       # Web scraping modules
│   └── ui/             # Streamlit frontend
├── tests/              # Test suite
├── config/             # Configuration files
├── docs/               # Documentation
├── docker/             # Docker configuration
├── requirements.txt    # Python dependencies
└── docker-compose.yml  # Container orchestration
```

## API Documentation

The API documentation is available at `/api/docs` when running the application. It provides detailed information about all available endpoints, request/response schemas, and authentication requirements.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers. 