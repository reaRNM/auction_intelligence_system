# Secrets Management

This document outlines how to handle sensitive information in the Auction Intelligence System.

## Types of Secrets

1. **API Keys**
   - Amazon API keys
   - eBay API keys
   - Shipping carrier API keys
   - External service API keys

2. **Database Credentials**
   - Database URLs
   - Usernames
   - Passwords

3. **Authentication Tokens**
   - JWT secrets
   - OAuth tokens
   - Session keys

4. **Encryption Keys**
   - Data encryption keys
   - SSL/TLS certificates
   - SSH keys

## Storing Secrets

### Development Environment
- Use `.env` files (not committed to git)
- Use local environment variables
- Use development key vaults

### Production Environment
- Use GitHub Secrets for CI/CD
- Use environment variables in deployment
- Use cloud key vaults (AWS Secrets Manager, Azure Key Vault)

## GitHub Secrets

Required secrets for GitHub Actions:

```yaml
SNYK_TOKEN: # Snyk API token for security scanning
SONAR_TOKEN: # SonarCloud token for code analysis
GITHUB_TOKEN: # GitHub token for repository access
AWS_ACCESS_KEY_ID: # AWS access key for deployment
AWS_SECRET_ACCESS_KEY: # AWS secret key for deployment
DB_URL: # Database connection URL
```

## Local Development Setup

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Fill in the required values in `.env`

3. Never commit `.env` to version control

## Security Best Practices

1. **Never** commit secrets to version control
2. Rotate secrets regularly
3. Use different secrets for different environments
4. Follow the principle of least privilege
5. Audit secret usage regularly
6. Use secret scanning tools
7. Encrypt secrets at rest
8. Use secure channels for secret transmission

## Emergency Procedures

If secrets are compromised:

1. Immediately rotate all affected secrets
2. Audit systems for unauthorized access
3. Update documentation
4. Notify affected parties
5. Review access logs
6. Update security policies if needed

## Tools and Resources

- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/)
- [HashiCorp Vault](https://www.vaultproject.io/)

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