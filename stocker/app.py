"""Main application entry point for STOCKER Pro.

This module provides the main entry point for the STOCKER Pro application,
handling command-line arguments, configuration, and initialization of the
various application components.
"""

import argparse
import os
import sys
from enum import Enum
from typing import Dict, List, Optional, Any

from stocker.core.config.settings import Settings, get_settings
from stocker.core.logging import configure_logging, get_logger
from stocker.core.exceptions import StockerException

# Initialize logger
logger = get_logger(__name__)


class AppMode(str, Enum):
    """Application modes for STOCKER Pro."""
    API = "api"          # Run as API server
    UI = "ui"            # Run as UI dashboard
    CLI = "cli"          # Run as command-line interface
    TRAIN = "train"      # Train models
    PREDICT = "predict"  # Make predictions
    BACKTEST = "backtest"  # Run backtesting
    DEFAULT = "default"  # Default mode (UI)


class StockerApp:
    """Main application class for STOCKER Pro.
    
    This class handles initialization and running of the STOCKER Pro application
    in various modes (API, UI, CLI, etc.).
    """
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the application.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Load settings
        self.settings = get_settings(config_path)
        
        # Configure logging
        log_file = os.path.join(self.settings.logs_dir, "stocker.log")
        configure_logging(
            default_level=self.settings.debug and "DEBUG" or "INFO",
            log_file=log_file,
            console_logging=True,
            file_logging=True,
            use_json=self.settings.environment == "production"
        )
        
        logger.info(f"Initializing STOCKER Pro {self.settings.app_version} in {self.settings.environment} mode")
        
        # Initialize components based on mode
        self.components: Dict[str, Any] = {}
    
    def run(self, mode: AppMode = AppMode.DEFAULT, **kwargs) -> None:
        """Run the application in the specified mode.
        
        Args:
            mode: Application mode
            **kwargs: Additional arguments for the specific mode
        """
        logger.info(f"Running STOCKER Pro in {mode} mode")
        
        try:
            if mode == AppMode.API:
                self._run_api(**kwargs)
            elif mode == AppMode.UI:
                self._run_ui(**kwargs)
            elif mode == AppMode.CLI:
                self._run_cli(**kwargs)
            elif mode == AppMode.TRAIN:
                self._run_training(**kwargs)
            elif mode == AppMode.PREDICT:
                self._run_prediction(**kwargs)
            elif mode == AppMode.BACKTEST:
                self._run_backtest(**kwargs)
            else:  # Default mode
                self._run_ui(**kwargs)
        except Exception as e:
            logger.exception(f"Error running STOCKER Pro: {str(e)}")
            raise
    
    def _run_api(self, host: Optional[str] = None, port: Optional[int] = None, **kwargs) -> None:
        """Run the application as an API server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional arguments
        """
        from stocker.interfaces.api.server import create_app, run_app
        
        app = create_app(self.settings)
        run_app(
            app,
            host=host or self.settings.api.host,
            port=port or self.settings.api.port,
            **kwargs
        )
    
    def _run_ui(self, debug: Optional[bool] = None, **kwargs) -> None:
        """Run the application as a UI dashboard.
        
        Args:
            debug: Whether to run in debug mode
            **kwargs: Additional arguments
        """
        from stocker.interfaces.ui.dashboard import create_dashboard, run_dashboard
        
        dashboard = create_dashboard(self.settings)
        run_dashboard(
            dashboard,
            debug=debug if debug is not None else self.settings.debug,
            **kwargs
        )
    
    def _run_cli(self, args: Optional[List[str]] = None, **kwargs) -> None:
        """Run the application as a command-line interface.
        
        Args:
            args: Command-line arguments
            **kwargs: Additional arguments
        """
        from stocker.interfaces.cli.commands import run_cli
        
        run_cli(self.settings, args=args, **kwargs)
    
    def _run_training(self, model_type: Optional[str] = None, **kwargs) -> None:
        """Run model training.
        
        Args:
            model_type: Type of model to train
            **kwargs: Additional arguments
        """
        from stocker.services.training import train_model
        
        train_model(
            model_type=model_type or self.settings.model_type,
            settings=self.settings,
            **kwargs
        )
    
    def _run_prediction(self, model_name: Optional[str] = None, **kwargs) -> None:
        """Run model prediction.
        
        Args:
            model_name: Name of model to use for prediction
            **kwargs: Additional arguments
        """
        from stocker.services.prediction import make_predictions
        
        make_predictions(
            model_name=model_name or self.settings.model_name,
            settings=self.settings,
            **kwargs
        )
    
    def _run_backtest(self, strategy: Optional[str] = None, **kwargs) -> None:
        """Run backtesting.
        
        Args:
            strategy: Strategy to backtest
            **kwargs: Additional arguments
        """
        from stocker.services.strategy import backtest_strategy
        
        backtest_strategy(
            strategy=strategy,
            settings=self.settings,
            **kwargs
        )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="STOCKER Pro - Advanced Stock Analysis and Portfolio Management")
    
    # General arguments
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        default=None
    )
    parser.add_argument(
        "--debug",
        help="Enable debug mode",
        action="store_true"
    )
    parser.add_argument(
        "--mode",
        help="Application mode",
        choices=[mode.value for mode in AppMode],
        default=AppMode.DEFAULT.value
    )
    
    # API mode arguments
    parser.add_argument(
        "--host",
        help="Host to bind to (API mode)",
        default=None
    )
    parser.add_argument(
        "--port",
        help="Port to bind to (API mode)",
        type=int,
        default=None
    )
    
    # Training mode arguments
    parser.add_argument(
        "--model-type",
        help="Type of model to train (training mode)",
        default=None
    )
    
    # Prediction mode arguments
    parser.add_argument(
        "--model-name",
        help="Name of model to use for prediction (prediction mode)",
        default=None
    )
    
    # Backtest mode arguments
    parser.add_argument(
        "--strategy",
        help="Strategy to backtest (backtest mode)",
        default=None
    )
    
    # Symbols argument for various modes
    parser.add_argument(
        "--symbols",
        help="Comma-separated list of stock symbols",
        default=None
    )
    
    return parser.parse_args()


def main() -> int:
    """Main function for the STOCKER Pro application.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Parse command-line arguments
        args = parse_args()
        
        # Create and run the application
        app = StockerApp(config_path=args.config)
        
        # Convert symbols string to list if provided
        kwargs = {}
        if args.symbols:
            kwargs["symbols"] = args.symbols.split(",")
        
        # Add other arguments
        if args.host:
            kwargs["host"] = args.host
        if args.port:
            kwargs["port"] = args.port
        if args.model_type:
            kwargs["model_type"] = args.model_type
        if args.model_name:
            kwargs["model_name"] = args.model_name
        if args.strategy:
            kwargs["strategy"] = args.strategy
        if args.debug:
            kwargs["debug"] = args.debug
        
        # Run the application in the specified mode
        app.run(mode=AppMode(args.mode), **kwargs)
        
        return 0
    except StockerException as e:
        logger.error(f"Application error: {str(e)}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
