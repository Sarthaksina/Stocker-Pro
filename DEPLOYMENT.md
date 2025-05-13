# STOCKER Pro API Deployment Guide

This document provides instructions for deploying the STOCKER Pro API in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Manual Deployment](#manual-deployment)
- [SSL Configuration](#ssl-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)

## Prerequisites

Before deploying the STOCKER Pro API, ensure you have the following:

- Python 3.10 or later
- PostgreSQL 14 or later
- Redis 7 or later
- Docker and Docker Compose (for containerized deployment)
- Kubernetes cluster (for Kubernetes deployment)

## Environment Variables

The STOCKER Pro API is configured using environment variables. Copy the `.env.example` file to `.env` and update the values as needed:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Key environment variables include:

- `STOCKER_ENVIRONMENT`: Set to `production` for production deployments
- `STOCKER_SECURITY_SECRET_KEY`: A secure random string for JWT token generation
- `STOCKER_DATABASE_URL`: PostgreSQL connection string
- `STOCKER_REDIS_URL`: Redis connection string
- `STOCKER_ALPHA_VANTAGE_API_KEY`: Your Alpha Vantage API key

See the `.env.example` file for a complete list of available environment variables.

## Docker Deployment

### Building the Docker Image

```bash
# Build the Docker image
docker build -t stocker-pro-api:latest .
```

### Running with Docker Compose

The easiest way to deploy the STOCKER Pro API is using Docker Compose, which will set up the API, database, Redis, and monitoring tools:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

The API will be available at http://localhost:8000.

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured to access your cluster
- Helm (optional, for package management)

### Deployment Steps

1. Create the namespace:

```bash
kubectl create namespace stocker
```

2. Create the secrets (replace placeholders with actual values):

```bash
cp kubernetes/secrets-template.yaml kubernetes/secrets.yaml
# Edit secrets.yaml with your actual secrets
kubectl apply -f kubernetes/secrets.yaml -n stocker
```

3. Create persistent volumes:

```bash
kubectl apply -f kubernetes/persistent-volumes.yaml -n stocker
```

4. Deploy the database and Redis:

```bash
kubectl apply -f kubernetes/database-deployment.yaml -n stocker
kubectl apply -f kubernetes/redis-deployment.yaml -n stocker
```

5. Deploy the API:

```bash
kubectl apply -f kubernetes/api-deployment.yaml -n stocker
kubectl apply -f kubernetes/api-service.yaml -n stocker
```

6. Deploy the ingress (if using):

```bash
kubectl apply -f kubernetes/api-ingress.yaml -n stocker
```

### Scaling the API

To scale the API horizontally:

```bash
kubectl scale deployment stocker-api -n stocker --replicas=5
```

## Manual Deployment

### System Requirements

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Nginx (for production)

### Installation Steps

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

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the API:

```bash
python -m stocker.interfaces.api.main
```

### Production Deployment with Gunicorn and Nginx

1. Install Gunicorn:

```bash
pip install gunicorn
```

2. Create a systemd service file (on Linux):

```ini
[Unit]
Description=STOCKER Pro API
After=network.target

[Service]
User=stocker
WorkingDirectory=/path/to/stocker-pro
EnvironmentFile=/path/to/stocker-pro/.env
ExecStart=/path/to/stocker-pro/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 stocker.interfaces.api.main:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

3. Set up Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## SSL Configuration

### Using Let's Encrypt with Nginx

1. Install Certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx
```

2. Obtain and configure SSL certificate:

```bash
sudo certbot --nginx -d api.yourdomain.com
```

### Using SSL with Docker Compose

Update the `docker-compose.yml` file to mount SSL certificates and configure the API to use SSL:

```yaml
api:
  # ... other configuration ...
  environment:
    - STOCKER_SECURITY_SSL_ENABLED=true
    - STOCKER_SECURITY_SSL_CERT_FILE=/app/ssl/cert.pem
    - STOCKER_SECURITY_SSL_KEY_FILE=/app/ssl/key.pem
  volumes:
    - ./ssl:/app/ssl
```

## Monitoring Setup

### Prometheus and Grafana

The Docker Compose configuration includes Prometheus and Grafana for monitoring. Access them at:

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (default credentials: admin/admin)

### Setting Up Grafana Dashboards

1. Log in to Grafana
2. Add Prometheus as a data source (URL: http://prometheus:9090)
3. Import the STOCKER Pro dashboard (available in the `monitoring` directory)

## Backup and Recovery

### Database Backup

```bash
# Docker Compose
docker-compose exec db pg_dump -U stocker stocker_db > backup.sql

# Kubernetes
kubectl exec -n stocker $(kubectl get pod -n stocker -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- pg_dump -U stocker stocker_db > backup.sql

# Direct PostgreSQL
pg_dump -U stocker stocker_db > backup.sql
```

### Database Restore

```bash
# Docker Compose
cat backup.sql | docker-compose exec -T db psql -U stocker stocker_db

# Kubernetes
cat backup.sql | kubectl exec -i -n stocker $(kubectl get pod -n stocker -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U stocker stocker_db

# Direct PostgreSQL
psql -U stocker stocker_db < backup.sql
```

## Troubleshooting

### Common Issues

1. **API fails to start**
   - Check environment variables
   - Verify database connection
   - Check logs: `docker-compose logs api` or `kubectl logs -n stocker deployment/stocker-api`

2. **Database connection issues**
   - Verify database credentials
   - Check if database service is running
   - Ensure network connectivity between API and database

3. **Rate limiting too aggressive**
   - Adjust `STOCKER_API_RATE_LIMIT_PER_MINUTE` in environment variables

### Viewing Logs

```bash
# Docker Compose
docker-compose logs -f api

# Kubernetes
kubectl logs -n stocker -l app=stocker-api -f

# Systemd
journalctl -u stocker-api.service -f
```
