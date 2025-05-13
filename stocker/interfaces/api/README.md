# STOCKER Pro API

This directory contains the production-grade API implementation for STOCKER Pro, built with FastAPI.

## Features

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

## Directory Structure

```
api/
├── __init__.py          # Package initialization
├── app.py               # FastAPI application factory
├── dependencies.py      # Dependency injection
├── schemas/             # Pydantic models for request/response
├── routes/              # API route handlers
├── middleware/          # Custom middleware
│   ├── __init__.py      # Middleware package
│   ├── logging.py       # Request logging middleware
│   ├── rate_limit.py    # Rate limiting middleware
│   ├── security.py      # Security headers middleware
│   └── version.py       # API version middleware
└── security.py          # Security utilities (JWT, passwords)
```

## Usage

### Running the API

```bash
uvicorn stocker.interfaces.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Configuration

The API is configured through environment variables or a .env file. See the settings module for available options.

Key configuration options:

```
# API Settings
STOCKER_API_HOST=127.0.0.1
STOCKER_API_PORT=8000
STOCKER_API_CORS_ORIGINS=["*"]
STOCKER_API_RATE_LIMITING_ENABLED=true
STOCKER_API_RATE_LIMIT_PER_MINUTE=60

# Security Settings
STOCKER_SECURITY_SECRET_KEY=your-secret-key-here
STOCKER_SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES=30
STOCKER_SECURITY_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### API Endpoints

- `/api/auth/*` - Authentication endpoints
- `/api/users/*` - User management
- `/api/stocks/*` - Stock data and analysis
- `/api/portfolios/*` - Portfolio management
- `/api/strategies/*` - Trading strategies

### Documentation

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI Schema: `/api/openapi.json`

## Development

### Adding New Routes

1. Create a new router in the routes directory
2. Define your endpoints using FastAPI decorators
3. Include the router in app.py

### Adding New Middleware

1. Create a new middleware class in the middleware directory
2. Add a helper function to add the middleware to the app
3. Update app.py to use the new middleware

### Testing

Tests for the API are located in the tests/interfaces/api directory. Run them with pytest:

```bash
pytest tests/interfaces/api
```
