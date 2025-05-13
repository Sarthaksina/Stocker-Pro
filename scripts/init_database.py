#!/usr/bin/env python
"""Database initialization script for STOCKER Pro.

This script initializes the database with tables and seed data.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from stocker.core.config.settings import get_settings
from stocker.core.logging import get_logger
from stocker.infrastructure.database.init_db import init_database

# Initialize logger
logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize STOCKER Pro database")
    parser.add_argument(
        "--connection-string",
        help="Database connection string (overrides environment variable)"
    )
    parser.add_argument(
        "--echo",
        action="store_true",
        help="Echo SQL statements"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Get settings
    settings = get_settings()
    
    # Log initialization
    logger.info(f"Initializing STOCKER Pro database")
    logger.info(f"Data directory: {settings.data_dir}")
    
    # Initialize database
    init_database(
        connection_string=args.connection_string,
        echo=args.echo
    )
    
    logger.info(f"Database initialization complete")


if __name__ == "__main__":
    main()
