"""Settings module for STOCKER Pro.

This module provides a comprehensive configuration system using Pydantic for validation
and environment variable loading. It preserves all functionality from the original
configuration implementation while adding modern features and better type safety.
"""

import os
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.env_settings import BaseSettings, SettingsConfigDict

# Environment variable prefix
ENV_PREFIX = "STOCKER_"

# Default configuration values
DEFAULT_DATA_DIR = "data"
DEFAULT_MONGODB_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "stocker_db"
STOCK_COLLECTION = "stocks"
DEFAULT_START_DATE = "2018-01-01"
DEFAULT_END_DATE = "2023-01-01"
APP_NAME = "STOCKER Pro"
VERSION = "1.0.0"
DEFAULT_LOG_FILE = "logs/stocker.log"
SUPPORTED_EXCHANGES = ["NSE", "BSE", "NYSE", "NASDAQ"]
DEFAULT_MODEL = "ensemble"
ENSEMBLE_WEIGHTS = {"lstm": 0.4, "xgboost": 0.3, "lightgbm": 0.3}
MAX_NEWS_ARTICLES = 50


class Environment(str, Enum):
    """Environment types for configuration"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class ConfigError(Exception):
    """Base exception for configuration errors"""
    pass


class ConfigValidationError(ConfigError):
    """Exception raised when configuration validation fails."""
    pass


class DataSourceSettings(BaseModel):
    """Settings for data sources"""
    # Yahoo Finance settings
    yahoo_finance_enabled: bool = True
    yahoo_cache_days: int = 7
    
    # Alpha Vantage settings
    alpha_vantage_enabled: bool = False
    alpha_vantage_api_key: str = ""
    alpha_vantage_requests_per_minute: int = 5
    
    # General data settings
    default_start_date: str = DEFAULT_START_DATE
    default_end_date: str = ""  # Empty means current date
    data_cache_dir: str = "cache"
    
    class Config:
        extra = "allow"


class ModelSettings(BaseModel):
    """Settings for prediction models"""
    # General model settings
    default_model: str = DEFAULT_MODEL
    model_save_dir: str = "models"
    
    # LSTM settings
    lstm_units: int = 50
    lstm_dropout: float = 0.2
    lstm_recurrent_dropout: float = 0.2
    lstm_epochs: int = 100
    lstm_batch_size: int = 32
    
    # XGBoost settings
    xgboost_max_depth: int = 6
    xgboost_learning_rate: float = 0.01
    xgboost_n_estimators: int = 1000
    xgboost_objective: str = "reg:squarederror"
    
    # LightGBM settings
    lightgbm_max_depth: int = 6
    lightgbm_learning_rate: float = 0.01
    lightgbm_n_estimators: int = 1000
    lightgbm_objective: str = "regression"
    
    # Ensemble settings
    ensemble_models: List[str] = ["lstm", "xgboost", "lightgbm"]
    ensemble_weights: List[float] = [0.4, 0.3, 0.3]
    
    class Config:
        extra = "allow"


class SecuritySettings(BaseModel):
    """Security settings for STOCKER Pro.
    
    This class contains security-related settings for the application.
    """
    secret_key: str = "stocker_secret_key_change_in_production"  # CHANGE THIS IN PRODUCTION!
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = False
    bcrypt_rounds: int = 12
    ssl_enabled: bool = False
    ssl_cert_file: str = ""
    ssl_key_file: str = ""
    allowed_hosts: List[str] = ["*"]
    
    class Config:
        env_prefix = "STOCKER_SECURITY_"
        extra = "allow"


class ApiSettings(BaseModel):
    """API settings for STOCKER Pro.
    
    This class contains settings for the API server.
    """
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    cors_origins: List[str] = ["*"]
    rate_limiting_enabled: bool = True
    rate_limit_per_minute: int = 60
    trusted_hosts: List[str] = ["127.0.0.1", "localhost"]
    root_path: str = ""  # For reverse proxy setups
    max_request_size_mb: int = 10  # Max request size in MB
    timeout_keep_alive: int = 5  # Seconds to keep connections alive
    workers: int = 1  # Number of worker processes
    log_level: str = "info"
    enable_prometheus: bool = False  # Enable Prometheus metrics
    enable_health_check: bool = True  # Enable health check endpoint
    alpha_vantage_requests_per_minute: int = 5
    
    class Config:
        env_prefix = "STOCKER_API_"
        extra = "allow"


class PortfolioSettings(BaseModel):
    """Settings for portfolio analytics"""
    risk_free_rate: float = 0.04
    benchmark_symbol: str = "SPY"
    rebalance_frequency: str = "monthly"
    optimization_method: str = "efficient_frontier"
    risk_aversion: float = 2.0
    max_position_size: float = 0.25
    min_position_size: float = 0.01
    target_volatility: float = 0.15
    presets_dir: str = "presets"
    cache_dir: str = "cache"
    
    class Config:
        extra = "allow"


class DatabaseSettings(BaseModel):
    """Settings for database connections"""
    mongodb_connection_string: str = DEFAULT_MONGODB_URI
    mongodb_database_name: str = DEFAULT_DB_NAME
    stock_data_collection: str = "stocks"
    models_collection: str = "models"
    portfolio_collection: str = "portfolios"
    user_collection: str = "users"
    news_collection: str = "news"
    username: Optional[str] = None
    password: Optional[str] = None
    extra: Dict[str, Any] = {}
    
    class Config:
        extra = "allow"


class AWSSettings(BaseModel):
    """Settings for AWS services"""
    access_key: str = ""
    secret_key: str = ""
    region: str = "us-east-1"
    bucket: str = ""
    extra: Dict[str, Any] = {}
    
    class Config:
        extra = "allow"


class DataSettings(BaseModel):
    """Settings for data sources and processing"""
    default_start_date: str = DEFAULT_START_DATE
    default_end_date: str = ""
    cache_dir: str = "cache"
    sources: List[str] = ["alpha_vantage"]
    missing_value_method: str = "ffill"
    technical_indicators: Dict[str, Any] = {
        "ma_windows": [5, 10, 20, 50, 200],
        "rsi_periods": [14],
        "macd_params": {"fast": 12, "slow": 26, "signal": 9},
        "bb_params": {"window": 20, "num_std": 2},
        "atr_periods": [14],
        "stoch_params": {"k_period": 14, "d_period": 3}
    }
    
    class Config:
        extra = "allow"


class IntelligenceSettings(BaseModel):
    """Settings for AI and intelligence features"""
    vector_store: Dict[str, Any] = {
        "provider": "chroma",
        "collection": "stocker_docs",
        "embedding_model": "all-MiniLM-L6-v2",
    }
    llm: Dict[str, Any] = {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 500,
    }
    news: Dict[str, Any] = {
        "sources": ["bloomberg", "cnbc", "reuters", "wsj"],
        "max_age_days": 30,
    }
    
    class Config:
        extra = "allow"


class UISettings(BaseModel):
    """Settings for user interface"""
    theme: str = "dark"
    default_chart_type: str = "candlestick"
    default_timeframe: str = "1d"
    
    class Config:
        extra = "allow"


class Settings(BaseSettings):
    """Main settings class for STOCKER Pro.
    
    This class combines all settings into a single, comprehensive configuration
    that can be loaded from environment variables and configuration files.
    """
    # Environment and project paths
    environment: Environment = Environment.DEVELOPMENT
    project_root: str = Field(default_factory=lambda: os.getcwd())
    data_dir: str = Field(default_factory=lambda: os.path.join(os.getcwd(), DEFAULT_DATA_DIR))
    logs_dir: str = "logs"
    models_dir: str = "models"
    artifacts_dir: str = "artifacts"
    
    # Application settings
    mode: str = "default"
    app_name: str = APP_NAME
    app_version: str = VERSION
    debug: bool = True
    
    # Data settings
    symbols: List[str] = ["AAPL", "MSFT", "GOOG", "AMZN", "META"]
    default_start_date: str = DEFAULT_START_DATE
    default_end_date: str = DEFAULT_END_DATE
    training_start_date: str = DEFAULT_START_DATE
    training_end_date: str = DEFAULT_END_DATE
    data_sources: List[str] = ["alpha_vantage"]
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_dir: str = "cache"
    
    # API keys
    alpha_vantage_api_key: Optional[str] = None
    thunder_compute_api_key: Optional[str] = None
    
    # Model settings
    model_type: str = "ensemble"
    model_name: Optional[str] = None
    model_path: Optional[str] = None
    model_params: Dict[str, Any] = {}
    hyperparameter_tuning: bool = False
    max_trials: int = 20
    early_stopping: bool = True
    
    # Feature settings
    target_col: str = "close"
    forecast_horizon: int = 1
    train_test_split: float = 0.8
    feature_selection_method: str = "importance"
    
    # Technical indicators
    ma_windows: List[int] = [5, 10, 20, 50, 200]
    rsi_periods: List[int] = [14]
    macd_params: Dict[str, int] = {"fast": 12, "slow": 26, "signal": 9}
    bb_params: Dict[str, Any] = {"window": 20, "num_std": 2}
    atr_periods: List[int] = [14]
    stoch_params: Dict[str, int] = {"k_period": 14, "d_period": 3}
    
    # UI settings
    ui_theme: str = "dark"
    default_chart_type: str = "candlestick"
    default_timeframe: str = "1d"
    
    # Intelligence settings
    vector_store_provider: str = "chroma"
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_provider: str = "openai"
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.1
    
    # Nested settings
    data_source: DataSourceSettings = Field(default_factory=DataSourceSettings)
    model_settings: ModelSettings = Field(default_factory=ModelSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    portfolio: PortfolioSettings = Field(default_factory=PortfolioSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    data: DataSettings = Field(default_factory=DataSettings)
    intelligence: IntelligenceSettings = Field(default_factory=IntelligenceSettings)
    ui: UISettings = Field(default_factory=UISettings)
    aws: Optional[AWSSettings] = None
    
    @validator('model_name', always=True)
    def set_model_name(cls, v, values):
        """Set model name if not provided"""
        if v is None:
            model_type = values.get('model_type', DEFAULT_MODEL)
            return f"{model_type}_{datetime.now().strftime('%Y%m%d')}"
        return v
    
    @root_validator(pre=False)
    def create_directories(cls, values):
        """Create necessary directories"""
        for dir_path in [
            values.get('data_dir'), 
            values.get('models_dir'), 
            values.get('logs_dir'), 
            values.get('artifacts_dir')
        ]:
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
        return values
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """Convert settings to dictionary, handling nested models"""
        exclude_none = kwargs.pop('exclude_none', True)
        result = super().dict(*args, exclude_none=exclude_none, **kwargs)
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary"""
        return cls(**config_dict)
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> 'Settings':
        """Load settings from a file (JSON or YAML)"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        if file_path.suffix.lower() == ".json":
            with open(file_path, "r") as f:
                config_dict = json.load(f)
        elif file_path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml
                with open(file_path, "r") as f:
                    config_dict = yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML configuration files")
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        return cls.from_dict(config_dict)
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save settings to a file (JSON or YAML)"""
        file_path = Path(file_path)
        config_dict = self.dict()
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save based on file extension
        if file_path.suffix.lower() == ".json":
            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)
        elif file_path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml
                with open(file_path, "w") as f:
                    yaml.dump(config_dict, f, default_flow_style=False)
            except ImportError:
                raise ImportError("PyYAML is required to save YAML configuration files")
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        extra="allow",
    )


# Create a global settings instance
settings = Settings()


def get_settings(config_path: Optional[str] = None) -> Settings:
    """Get the global settings instance or load from a file"""
    if config_path:
        return Settings.load_from_file(config_path)
    return settings


def get_alpha_vantage_client():
    """Get Alpha Vantage client with API key from settings"""
    from stocker.infrastructure.integrations.alpha_vantage.client import AlphaVantageClient
    
    api_key = settings.alpha_vantage_api_key
    if not api_key:
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    
    if not api_key:
        raise ConfigError("Alpha Vantage API key not found in settings or environment variables")
    
    return AlphaVantageClient(api_key=api_key)
