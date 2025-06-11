# STOCKER Pro

STOCKER Pro is an advanced stock analysis and portfolio management system with a production-grade API built using FastAPI, SQLAlchemy, and modern Python practices.

## Features

- **Stock Data Analysis**: Technical indicators, historical data, and price predictions
- **Portfolio Management**: Track investments, analyze performance, and optimize allocations
- **Trading Strategies**: Implement and backtest custom trading strategies
- **Machine Learning Models**: Price prediction using LSTM, XGBoost, and ensemble models
- **Production-Grade API**: Secure, scalable, and monitored REST API

## Architecture

STOCKER Pro follows a clean architecture approach with clear separation of concerns:

- **Domain Layer**: Core business entities and logic
- **Application Layer**: Use cases and services
- **Infrastructure Layer**: External systems integration and persistence
- **Interface Layer**: API endpoints and UI components

For more details, see [PLANNING.md](PLANNING.md).

## API Features

### Security
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- Security headers middleware (HSTS, CSP, X-Content-Type-Options, etc.)
- CORS protection with configurable origins
- Rate limiting to prevent abuse
- Input validation with Pydantic

### Monitoring and Observability
- Comprehensive health check endpoint with system metrics
- Request logging middleware with timing information
- Structured JSON logging for better analysis
- Version headers for API versioning

### Error Handling
- Production-friendly exception handling
- Detailed error responses in development, sanitized in production
- Consistent error format across the API

### API Documentation
- Custom Swagger UI integration
- ReDoc integration
- OpenAPI schema with security definitions

## Getting Started

### Prerequisites

- Python 3.10 or later
- PostgreSQL 14 or later
- Redis 7 or later (optional, for caching and task queues)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/stocker-pro.git
cd stocker-pro
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Poetry (if you don't have it already):
   Refer to the official Poetry documentation for installation instructions: https://python-poetry.org/docs/#installation

4. Install project dependencies using Poetry:

```bash
poetry install
```

5. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the API:

```bash
python -m stocker.interfaces.api.main
```

The API will be available at http://localhost:8000.

### Docker Deployment

You can also run STOCKER Pro using Docker:

```bash
# Build and start all services
docker-compose up -d
```

For more deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md).

## API Documentation

Once the API is running, you can access the documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Code Quality

STOCKER Pro uses several tools to maintain code quality. These tools are included in the project's development dependencies and will be installed when you run `poetry install` (ensure your Poetry configuration includes dev dependencies, or run `poetry install --with dev` if they are in a separate group and not installed by default):

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **mypy**: Type checking
- **Bandit**: Security scanning
- **pre-commit**: Automated checks before commits

Set up pre-commit hooks (after installing dependencies with Poetry):

```bash
pre-commit install
```

### Testing

Run tests with pytest:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=stocker
```

## CI/CD Pipeline

STOCKER Pro uses GitHub Actions for continuous integration and deployment. The pipeline includes:

- Automated testing
- Code quality checks
- Docker image building
- Deployment to staging and production environments

For more details, see [CI_CD.md](CI_CD.md).

## Project Structure

```
stocker-pro/
├── stocker/                 # Main package
│   ├── app.py               # Main application (placeholder)
│   ├── core/                # Core functionality
│   │   ├── config/          # Configuration management
│   │   ├── exceptions.py    # Exception hierarchy
│   │   ├── logging/         # Logging configuration
│   │   └── utils/           # Utility functions
│   ├── domain/              # Domain models
│   ├── infrastructure/      # External systems integration
│   │   └── database/        # Database models and repositories
│   ├── services/            # Business logic services
│   └── interfaces/          # User interfaces
│       └── api/             # FastAPI application
├── tests/                   # Test suite
├── kubernetes/              # Kubernetes manifests
├── migrations/              # Database migrations (env.py, script.py.mako, versions/)
├── .github/                 # GitHub configuration
│   └── workflows/           # GitHub Actions workflows
├── alembic.ini              # Alembic configuration
├── pyproject.toml          # Project configuration (including dependencies)
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── PLANNING.md             # Architecture and planning
├── TASK.md                 # Task tracking
├── DEPLOYMENT.md           # Deployment guide
└── CI_CD.md                # CI/CD documentation
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
