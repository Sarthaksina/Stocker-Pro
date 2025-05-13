"""Main entry point for STOCKER Pro API.

This module provides a script to run the FastAPI application.
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

from stocker.core.config.settings import get_settings, Environment
from stocker.core.logging import get_logger, setup_logging
from stocker.interfaces.api.app import create_app

# Initialize logger
setup_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = create_app()


def run_server(host=None, port=None, reload=None, workers=None, log_level=None):
    """Run the API server with the specified configuration.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Whether to enable auto-reload
        workers: Number of worker processes
        log_level: Logging level
    """
    # Get settings
    settings = get_settings()
    
    # Override settings with arguments if provided
    host = host or settings.api.host
    port = port or settings.api.port
    reload = reload if reload is not None else settings.api.reload
    workers = workers or settings.api.workers
    log_level = log_level or settings.log_level.lower()
    
    # Determine if we're in production
    is_production = settings.environment == Environment.PRODUCTION
    
    # Configure SSL if enabled in production
    ssl_keyfile = None
    ssl_certfile = None
    if is_production and settings.security.ssl_enabled:
        ssl_keyfile = settings.security.ssl_key_file
        ssl_certfile = settings.security.ssl_cert_file
        
        # Validate SSL configuration
        if not ssl_keyfile or not ssl_certfile:
            logger.error("SSL is enabled but key or cert file is missing")
            sys.exit(1)
        
        if not os.path.exists(ssl_keyfile) or not os.path.exists(ssl_certfile):
            logger.error("SSL key or cert file does not exist")
            sys.exit(1)
    
    # Log startup message
    logger.info(
        f"Starting STOCKER Pro API on {host}:{port} ({settings.environment})",
        extra={
            "host": host,
            "port": port,
            "environment": settings.environment,
            "workers": workers,
            "reload": reload,
            "ssl_enabled": bool(ssl_keyfile and ssl_certfile)
        }
    )
    
    # Run server
    uvicorn.run(
        "stocker.interfaces.api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
        access_log=True,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        timeout_keep_alive=settings.api.timeout_keep_alive,
        limit_max_requests=settings.api.get("limit_max_requests", None),
        proxy_headers=is_production,  # Enable proxy headers in production
        forwarded_allow_ips="*" if is_production else None  # Trust forwarded headers in production
    )


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the STOCKER Pro API server")
    parser.add_argument("--host", help="Host to bind to")
    parser.add_argument("--port", type=int, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    parser.add_argument("--log-level", help="Logging level")
    
    args = parser.parse_args()
    
    # Run server with command line arguments
    run_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )
