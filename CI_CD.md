# STOCKER Pro CI/CD Pipeline

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the STOCKER Pro API.

## Overview

The STOCKER Pro CI/CD pipeline automates testing, building, and deploying the API to different environments. The pipeline is implemented using GitHub Actions and consists of two main workflows:

1. **Continuous Integration (CI)**: Runs tests, linting, and builds Docker images
2. **Continuous Deployment (CD)**: Deploys the application to staging and production environments

## CI Workflow

The CI workflow is defined in `.github/workflows/continuous-integration.yml` and includes the following stages:

### Testing Stage

- **Environment Setup**: Sets up Python and spins up PostgreSQL and Redis services for testing
- **Code Quality Checks**:
  - Linting with flake8
  - Code formatting with black
  - Import sorting with isort
  - Type checking with mypy
- **Unit and Integration Tests**: Runs pytest with coverage reporting
- **Coverage Reporting**: Uploads coverage reports to Codecov

### Build Stage

- **Docker Image Building**: Builds the Docker image using the multi-stage Dockerfile
- **Image Tagging**: Tags images based on branch, commit SHA, and version tags
- **Image Publishing**: Pushes images to GitHub Container Registry (ghcr.io)

## CD Workflow

The CD workflow is defined in `.github/workflows/cd.yml` and includes the following stages:

### Staging Deployment

- **Trigger**: Automatically triggered when CI passes on the `develop` branch
- **Environment**: Deploys to the staging environment
- **Secret Management**: Updates Kubernetes secrets with environment-specific values
- **Deployment**: Updates the Kubernetes deployment with the new image
- **Verification**: Verifies the deployment was successful
- **Notification**: Sends Slack notifications about deployment status

### Production Deployment

- **Trigger**: Automatically triggered when CI passes on the `main` branch or when a release is published
- **Environment**: Deploys to the production environment
- **Secret Management**: Updates Kubernetes secrets with environment-specific values
- **Deployment**: Updates the Kubernetes deployment with the new image
- **Verification**: Verifies the deployment was successful
- **Notification**: Sends Slack notifications about deployment status

## Setup Instructions

### Prerequisites

- GitHub repository with the STOCKER Pro codebase
- Kubernetes clusters for staging and production environments
- GitHub Actions enabled on the repository

### GitHub Secrets Configuration

The following secrets need to be configured in the GitHub repository settings:

#### For Both Environments

- `SLACK_WEBHOOK`: Webhook URL for Slack notifications

#### For Staging Environment

- `KUBE_CONFIG`: Base64-encoded kubeconfig file for the staging Kubernetes cluster
- `SECURITY_SECRET_KEY`: Secret key for JWT token generation
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name

#### For Production Environment

- `KUBE_CONFIG`: Base64-encoded kubeconfig file for the production Kubernetes cluster
- `SECURITY_SECRET_KEY`: Secret key for JWT token generation
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API key
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name

### Kubernetes Setup

1. Create the necessary namespaces:

```bash
kubectl create namespace stocker-staging
kubectl create namespace stocker-production
```

2. Apply the Kubernetes manifests to both environments:

```bash
# For staging
kubectl apply -f kubernetes/persistent-volumes.yaml -n stocker-staging
kubectl apply -f kubernetes/database-deployment.yaml -n stocker-staging
kubectl apply -f kubernetes/redis-deployment.yaml -n stocker-staging
kubectl apply -f kubernetes/api-deployment.yaml -n stocker-staging
kubectl apply -f kubernetes/api-service.yaml -n stocker-staging
kubectl apply -f kubernetes/api-ingress.yaml -n stocker-staging

# For production
kubectl apply -f kubernetes/persistent-volumes.yaml -n stocker-production
kubectl apply -f kubernetes/database-deployment.yaml -n stocker-production
kubectl apply -f kubernetes/redis-deployment.yaml -n stocker-production
kubectl apply -f kubernetes/api-deployment.yaml -n stocker-production
kubectl apply -f kubernetes/api-service.yaml -n stocker-production
kubectl apply -f kubernetes/api-ingress.yaml -n stocker-production
```
Kubernetes resources are now deployed using Kustomize. Refer to the Kubernetes deployment section in `DEPLOYMENT.MD` for more details.

## Workflow

### Development Workflow

1. Developers work on feature branches
2. Pull requests are created to merge into the `develop` branch
3. CI runs on pull requests to verify code quality and tests
4. When a pull request is merged to `develop`, CI runs again and triggers the CD pipeline
5. The CD pipeline deploys to the staging environment
6. QA testing is performed on the staging environment

### Release Workflow

1. When ready for production, a pull request is created from `develop` to `main`
2. CI runs on the pull request to verify code quality and tests
3. When the pull request is merged to `main`, CI runs again and triggers the CD pipeline
4. The CD pipeline deploys to the production environment
5. Alternatively, a GitHub release can be created to trigger a production deployment with a specific version tag

## Monitoring and Troubleshooting

### Monitoring Deployments

- GitHub Actions workflow runs can be monitored in the "Actions" tab of the repository
- Deployment status notifications are sent to the configured Slack channel
- Kubernetes deployments can be monitored using kubectl:

```bash
kubectl get deployments -n stocker-staging
kubectl get deployments -n stocker-production
```

### Troubleshooting

#### CI Issues

- Check the GitHub Actions logs in the "Actions" tab
- Verify that all tests are passing locally
- Ensure all dependencies are correctly specified in `pyproject.toml`.

#### CD Issues

- Check the GitHub Actions logs in the "Actions" tab
- Verify Kubernetes secrets are correctly configured
- Check Kubernetes deployment status and logs:

```bash
kubectl describe deployment stocker-api -n stocker-staging
kubectl logs -l app=stocker-api -n stocker-staging
```

## Best Practices

1. **Never commit secrets** to the repository
2. Always run tests locally before pushing changes
3. Keep the `main` branch stable and production-ready at all times
4. Use semantic versioning for releases
5. Write meaningful commit messages and PR descriptions
6. Review code changes thoroughly before merging
7. Monitor deployments to catch issues early
