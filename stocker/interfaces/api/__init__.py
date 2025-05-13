"""API interface for STOCKER Pro.

This package provides a FastAPI application for exposing STOCKER Pro functionality
through a RESTful API.
"""

from stocker.interfaces.api.app import create_app

__all__ = ["create_app"]
