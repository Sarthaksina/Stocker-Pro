# STOCKER Pro API Dockerfile
# Multi-stage build for a production-ready Python FastAPI application

# Stage 1: Build dependencies
FROM python:3.10-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Runtime image
FROM python:3.10-slim

WORKDIR /app

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" stocker

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data /app/static \
    && chown -R stocker:stocker /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    STOCKER_ENVIRONMENT=production \
    STOCKER_LOG_LEVEL=info

# Switch to non-root user
USER stocker

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "stocker.interfaces.api.main", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
