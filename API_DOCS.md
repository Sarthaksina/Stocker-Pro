# STOCKER Pro API Documentation

## Overview

The STOCKER Pro API provides a comprehensive set of endpoints for stock market data analysis, portfolio management, and trading strategy implementation. This document provides detailed information about the API endpoints, authentication, error handling, and usage examples.

## Base URL

- **Production**: `https://api.stockerpro.example.com`
- **Staging**: `https://staging-api.stockerpro.example.com`

## API Versioning

The API supports versioning to ensure backward compatibility. You can specify the API version in three ways:

1. **URL Path**: `/v1/stocks`
2. **Query Parameter**: `/stocks?version=1`
3. **Header**: `X-API-Version: 1`

If no version is specified, the API defaults to the latest version.

## Authentication

The API supports two authentication methods:

### JWT Authentication

1. Obtain a token by calling the `/auth/login` endpoint
2. Include the token in the Authorization header: `Authorization: Bearer {token}`

```bash
# Example: Login and get token
curl -X POST https://api.stockerpro.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Example: Use token in request
curl https://api.stockerpro.example.com/v1/stocks \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### API Key Authentication

Include your API key in the `X-API-Key` header:

```bash
curl https://api.stockerpro.example.com/v1/stocks \
  -H "X-API-Key: your_api_key"
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Current limits are:

- **Authenticated users**: 120 requests per minute
- **Unauthenticated users**: 60 requests per minute

Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: Maximum number of requests per minute
- `X-RateLimit-Remaining`: Number of requests remaining in the current window
- `X-RateLimit-Reset`: Time in seconds until the rate limit resets

When the rate limit is exceeded, the API returns a `429 Too Many Requests` response.

## Error Handling

The API returns consistent error responses with the following structure:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-05-13T00:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "path": "/v1/stocks/invalid"
}
```

Common error codes:

| Status Code | Error Code | Description |
|-------------|------------|-------------|
| 400 | BAD_REQUEST | Invalid request parameters |
| 401 | UNAUTHORIZED | Authentication required |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 422 | VALIDATION_ERROR | Request validation failed |
| 429 | TOO_MANY_REQUESTS | Rate limit exceeded |
| 500 | INTERNAL_SERVER_ERROR | Server error |

## Endpoints

### Authentication

#### Login

```
POST /auth/login
```

Request body:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2025-05-14T00:00:00Z",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "your_username"
}
```

#### Get Current User

```
GET /auth/me
```

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "your_username",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "roles": ["user"],
  "is_active": true,
  "preferences": {}
}
```

### Stocks

#### List Stocks

```
GET /v1/stocks
```

Query parameters:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 100, max: 500)
- `search`: Search term for stock name or symbol
- `exchange`: Filter by exchange
- `sector`: Filter by sector

Response:

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "market_cap": 2500000000000,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-05-13T00:00:00Z"
    },
    ...
  ],
  "total": 5000,
  "page": 1,
  "limit": 100,
  "pages": 50
}
```

#### Get Stock

```
GET /v1/stocks/{symbol}
```

Query parameters:

- `include_prices`: Include historical prices (default: false)

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "market_cap": 2500000000000,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-05-13T00:00:00Z",
  "prices": [
    {
      "date": "2025-05-13",
      "open": 150.0,
      "high": 155.0,
      "low": 149.0,
      "close": 152.0,
      "adjusted_close": 152.0,
      "volume": 100000000
    },
    ...
  ]
}
```

#### Get Stock Prices

```
GET /v1/stocks/{symbol}/prices
```

Query parameters:

- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `interval`: Data interval (daily, weekly, monthly)

Response:

```json
{
  "symbol": "AAPL",
  "prices": [
    {
      "date": "2025-05-13",
      "open": 150.0,
      "high": 155.0,
      "low": 149.0,
      "close": 152.0,
      "adjusted_close": 152.0,
      "volume": 100000000
    },
    ...
  ]
}
```

### Portfolios

#### List Portfolios

```
GET /v1/portfolios
```

Response:

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "My Portfolio",
      "description": "Long-term investment portfolio",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-05-13T00:00:00Z",
      "total_value": 100000.0,
      "cash_balance": 10000.0,
      "positions_count": 10
    },
    ...
  ],
  "total": 5,
  "page": 1,
  "limit": 100,
  "pages": 1
}
```

#### Create Portfolio

```
POST /v1/portfolios
```

Request body:

```json
{
  "name": "New Portfolio",
  "description": "Growth investment strategy",
  "initial_balance": 50000.0
}
```

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "New Portfolio",
  "description": "Growth investment strategy",
  "created_at": "2025-05-13T00:00:00Z",
  "updated_at": "2025-05-13T00:00:00Z",
  "total_value": 50000.0,
  "cash_balance": 50000.0,
  "positions_count": 0
}
```

#### Get Portfolio

```
GET /v1/portfolios/{portfolio_id}
```

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Portfolio",
  "description": "Long-term investment portfolio",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-05-13T00:00:00Z",
  "total_value": 100000.0,
  "cash_balance": 10000.0,
  "positions": [
    {
      "stock_id": "550e8400-e29b-41d4-a716-446655440000",
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "quantity": 100.0,
      "average_price": 150.0,
      "current_price": 152.0,
      "market_value": 15200.0,
      "profit_loss": 200.0,
      "profit_loss_percent": 1.33
    },
    ...
  ]
}
```

### Strategies

#### List Strategies

```
GET /v1/strategies
```

Response:

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Moving Average Crossover",
      "description": "Strategy based on moving average crossovers",
      "strategy_type": "technical",
      "parameters": {
        "short_window": 50,
        "long_window": 200
      },
      "is_active": true,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-05-13T00:00:00Z"
    },
    ...
  ],
  "total": 5,
  "page": 1,
  "limit": 100,
  "pages": 1
}
```

#### Run Strategy

```
POST /v1/strategies/{strategy_id}/run
```

Request body:

```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "start_date": "2025-01-01",
  "end_date": "2025-05-13"
}
```

Response:

```json
{
  "strategy_id": "550e8400-e29b-41d4-a716-446655440000",
  "signals": [
    {
      "symbol": "AAPL",
      "signal_type": "BUY",
      "strength": 0.8,
      "generated_at": "2025-05-13T00:00:00Z",
      "parameters": {
        "short_ma": 155.0,
        "long_ma": 150.0
      }
    },
    ...
  ]
}
```

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (default: 1)
- `limit`: Items per page (default: 100, max: 500)

Paginated responses include the following metadata:

```json
{
  "items": [...],
  "total": 500,  // Total number of items
  "page": 1,     // Current page
  "limit": 100,  // Items per page
  "pages": 5     // Total number of pages
}
```

## Filtering and Sorting

List endpoints support filtering and sorting with the following query parameters:

- `sort`: Field to sort by (prefix with `-` for descending order)
- `filter`: Field-specific filters

Example:

```
GET /v1/stocks?sort=-market_cap&filter[exchange]=NASDAQ&filter[sector]=Technology
```

## Webhooks

The API supports webhooks for real-time notifications. You can configure webhooks in your account settings to receive notifications for the following events:

- Price alerts
- Strategy signals
- Portfolio updates

Webhook payloads include a signature header (`X-Stocker-Signature`) for verification.

## SDKs and Client Libraries

Official client libraries are available for the following languages:

- Python: [stocker-python](https://github.com/stockerpro/stocker-python)
- JavaScript: [stocker-js](https://github.com/stockerpro/stocker-js)
- Java: [stocker-java](https://github.com/stockerpro/stocker-java)

## API Status and Uptime

You can check the current API status and uptime at [status.stockerpro.example.com](https://status.stockerpro.example.com).

## Support

If you have any questions or need assistance, please contact our support team:

- Email: [api-support@stockerpro.example.com](mailto:api-support@stockerpro.example.com)
- Documentation: [docs.stockerpro.example.com](https://docs.stockerpro.example.com)
- API Status: [status.stockerpro.example.com](https://status.stockerpro.example.com)
