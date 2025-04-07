# Contributing to Auction Intelligence System

## Code Style

### Python
- Follow PEP 8 guidelines
- Use Black for code formatting
- Use isort for import sorting
- Use flake8 for linting
- Maximum line length: 88 characters (Black default)
- Use type hints for all function parameters and return values
- Document all public functions and classes with docstrings

### TypeScript/React
- Use ESLint with Airbnb config
- Use Prettier for formatting
- Follow React best practices
- Use TypeScript strict mode
- Document components with JSDoc

### Automated Enforcement
```bash
# Install pre-commit hooks
pre-commit install

# Run all checks
pre-commit run --all-files
```

## Branch Strategy

### Feature Branches
- Branch from: `main`
- Naming: `feature/description`
- Example: `feature/add-shipping-calculator`

### Bug Fixes
- Branch from: `main`
- Naming: `fix/description`
- Example: `fix/rate-limit-handling`

### Hotfix Branches
- Branch from: `main`
- Naming: `hotfix/description`
- Example: `hotfix/security-vulnerability`

### Hotfix Process
1. Create hotfix branch from main
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/issue-description
   ```

2. Make necessary changes
   ```bash
   git add .
   git commit -m "fix: description of the fix"
   ```

3. Update version number
   ```bash
   # Update version in pyproject.toml
   # Update CHANGELOG.md
   git add .
   git commit -m "chore: bump version"
   ```

4. Merge to main and develop
   ```bash
   git checkout main
   git merge --no-ff hotfix/issue-description
   git tag -a v1.x.x -m "Hotfix v1.x.x"
   git push origin main --tags
   ```

5. Clean up
   ```bash
   git branch -d hotfix/issue-description
   ```

## Pull Request Process

1. Update documentation
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/path/to/test.py

# Run with coverage
pytest --cov=app tests/
```

### Performance Testing
```bash
# Run performance benchmarks
pytest tests/performance --benchmark-only

# Run load tests
locust -f tests/performance/locustfile.py
```

## Documentation

### API Documentation
- Use OpenAPI/Swagger annotations
- Document all endpoints
- Include request/response examples

### Code Documentation
- Use docstrings for all public functions
- Include type hints
- Document complex algorithms
- Add usage examples for private methods

## Release Process

1. Update version numbers
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Create pull request
6. Merge after review
7. Tag release
8. Deploy to production

## Getting Help

- Open an issue for bugs
- Use discussions for questions
- Join our Slack channel
- Contact maintainers directly

## License

By contributing, you agree that your contributions will be licensed under the project's license. 