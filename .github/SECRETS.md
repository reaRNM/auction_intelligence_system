# Required GitHub Secrets

This document outlines the required secrets for the CI/CD pipeline and development environment. **DO NOT** commit actual secret values to the repository.

## CI/CD Pipeline Secrets

### Docker Registry
- `DOCKER_USERNAME`: Username for Docker registry
- `DOCKER_PASSWORD`: Password/token for Docker registry

### Code Quality
- `SNYK_TOKEN`: API token for Snyk security scanning
- `CODECOV_TOKEN`: Token for Codecov coverage reporting

### API Keys
- `EBAY_API_KEY`: eBay API credentials
- `AMAZON_API_KEY`: Amazon API credentials
- `GOOGLE_API_KEY`: Google API credentials

### Database
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password

### Redis
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `REDIS_PASSWORD`: Redis password

### Monitoring
- `SENTRY_DSN`: Sentry error tracking DSN
- `NEW_RELIC_LICENSE_KEY`: New Relic license key

## Development Environment Secrets

### Local Development
- `LOCAL_DB_URL`: Local database connection string
- `LOCAL_REDIS_URL`: Local Redis connection string

### Testing
- `TEST_DB_URL`: Test database connection string
- `TEST_REDIS_URL`: Test Redis connection string

## Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with its corresponding value

## Secret Rotation

- API keys should be rotated every 90 days
- Database credentials should be rotated every 180 days
- Other secrets should be rotated annually or when compromised

## Access Control

- Repository administrators can manage secrets
- GitHub Actions can access secrets during workflow execution
- Local development requires manual secret configuration

## Security Notes

1. Never commit secrets to the repository
2. Use environment variables for local development
3. Rotate secrets regularly
4. Monitor secret usage
5. Limit secret access to necessary workflows
6. Use secret scanning tools
7. Follow the principle of least privilege 