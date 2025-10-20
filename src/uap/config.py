"""Centralized configuration management for UAP"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from .exceptions import ConfigurationError
from .logging_config import get_logger

logger = get_logger(__name__)


class Environment(str, Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """Database configuration"""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="uap", description="Database name")
    user: str = Field(default="uap", description="Database user")
    password: str = Field(default="", description="Database password")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_overflow: int = Field(default=20, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, description="Pool recycle time in seconds")
    
    @property
    def url(self) -> str:
        """Get database URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseModel):
    """Redis configuration"""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=20, description="Max connections")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(default=5, description="Socket connect timeout in seconds")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    
    @property
    def url(self) -> str:
        """Get Redis URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(default="json", description="Log format (json or console)")
    include_timestamps: bool = Field(default=True, description="Include timestamps")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    max_file_size: int = Field(default=10485760, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup files")


class SecurityConfig(BaseModel):
    """Security configuration"""
    secret_key: str = Field(default="", description="Secret key for encryption")
    jwt_secret: str = Field(default="", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, description="JWT expiration in seconds")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")


class MonitoringConfig(BaseModel):
    """Monitoring configuration"""
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")
    enable_tracing: bool = Field(default=True, description="Enable distributed tracing")
    tracing_endpoint: Optional[str] = Field(default=None, description="Tracing endpoint")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    enable_profiling: bool = Field(default=False, description="Enable profiling")


class ProtocolConfig(BaseModel):
    """Protocol configuration"""
    mcp_enabled: bool = Field(default=True, description="Enable MCP protocol")
    a2a_enabled: bool = Field(default=True, description="Enable A2A protocol")
    acp_enabled: bool = Field(default=True, description="Enable ACP protocol")
    default_timeout: int = Field(default=30, description="Default protocol timeout in seconds")
    max_retries: int = Field(default=3, description="Max retry attempts")
    retry_delay: float = Field(default=1.0, description="Retry delay in seconds")


class ReflectionConfig(BaseModel):
    """Reflection configuration"""
    enable_reflection: bool = Field(default=True, description="Enable reflection engine")
    reflection_interval: int = Field(default=300, description="Reflection interval in seconds")
    max_memory_entries: int = Field(default=10000, description="Max memory entries")
    cleanup_interval: int = Field(default=3600, description="Cleanup interval in seconds")
    enable_auto_optimization: bool = Field(default=True, description="Enable auto-optimization")


class UAPConfig(BaseSettings):
    """Main UAP configuration"""
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Service configuration
    service_name: str = Field(default="uap", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8000, description="Service port")
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Security configuration")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig, description="Monitoring configuration")
    protocol: ProtocolConfig = Field(default_factory=ProtocolConfig, description="Protocol configuration")
    reflection: ReflectionConfig = Field(default_factory=ReflectionConfig, description="Reflection configuration")
    
    # Feature flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict, description="Feature flags")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value"""
        if v not in [e.value for e in Environment]:
            raise ValueError(f"Invalid environment: {v}")
        return v
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate port number"""
        if not 1 <= v <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.environment == Environment.TESTING
    
    def get_feature_flag(self, flag: str, default: bool = False) -> bool:
        """Get feature flag value"""
        return self.feature_flags.get(flag, default)
    
    def set_feature_flag(self, flag: str, value: bool) -> None:
        """Set feature flag value"""
        self.feature_flags[flag] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return self.model_dump()
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file"""
        try:
            config_dict = self.to_dict()
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            logger.info("Configuration saved to file", file_path=str(file_path))
        except Exception as e:
            logger.error("Failed to save configuration", file_path=str(file_path), error=str(e))
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> UAPConfig:
        """Load configuration from file"""
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            return cls(**config_dict)
        except Exception as e:
            logger.error("Failed to load configuration", file_path=str(file_path), error=str(e))
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    @classmethod
    def from_env(cls) -> UAPConfig:
        """Load configuration from environment variables"""
        try:
            return cls()
        except Exception as e:
            logger.error("Failed to load configuration from environment", error=str(e))
            raise ConfigurationError(f"Failed to load configuration from environment: {e}")


# Global configuration instance
_config: Optional[UAPConfig] = None


def get_config() -> UAPConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = UAPConfig.from_env()
    return _config


def set_config(config: UAPConfig) -> None:
    """Set global configuration instance"""
    global _config
    _config = config


def reload_config() -> UAPConfig:
    """Reload configuration from environment"""
    global _config
    _config = UAPConfig.from_env()
    return _config
