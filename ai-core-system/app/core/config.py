"""
Configuration management for the AI Core System.

This module handles all configuration settings using Pydantic Settings
for type safety and environment variable management.
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    redis_timeout: int = Field(default=5, env="REDIS_TIMEOUT")
    
    # Model Configuration
    model_config_path: str = Field(default="/app/models.json", env="MODEL_CONFIG_PATH")
    model_cache_dir: str = Field(default="/app/cache", env="MODEL_CACHE_DIR")
    default_model: str = Field(default="mistral-7b-instruct", env="DEFAULT_MODEL")
    model_load_timeout: int = Field(default=300, env="MODEL_LOAD_TIMEOUT")
    model_unload_timeout: int = Field(default=60, env="MODEL_UNLOAD_TIMEOUT")
    
    # Security Configuration
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR")
    max_prompt_length: int = Field(default=4096, env="MAX_PROMPT_LENGTH")
    max_tokens_per_request: int = Field(default=2048, env="MAX_TOKENS_PER_REQUEST")
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    enable_cors: bool = Field(default=True, env="ENABLE_CORS")
    
    # Authentication
    api_keys: List[str] = Field(default=[], env="API_KEYS")
    jwt_secret_key: str = Field(default="your-super-secret-jwt-key-change-this-in-production", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=30, env="JWT_EXPIRATION_MINUTES")
    
    # Monitoring and Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # Development Configuration
    reload_on_change: bool = Field(default=True, env="RELOAD_ON_CHANGE")
    enable_debug_endpoints: bool = Field(default=False, env="ENABLE_DEBUG_ENDPOINTS")
    enable_swagger_ui: bool = Field(default=True, env="ENABLE_SWAGGER_UI")
    enable_redoc: bool = Field(default=True, env="ENABLE_REDOC")
    
    # Additional fields from .env file
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    allowed_hosts: str = Field(default="*", env="ALLOWED_HOSTS")
    huggingface_token: Optional[str] = Field(default=None, env="HUGGINGFACE_TOKEN")
    
    # SSL Configuration (optional)
    ssl_enabled: bool = Field(default=False, env="SSL_ENABLED")
    ssl_cert_path: str = Field(default="", env="SSL_CERT_PATH")
    ssl_key_path: str = Field(default="", env="SSL_KEY_PATH")
    
    # Cloudflare Configuration (optional)
    cloudflare_enabled: bool = Field(default=False, env="CLOUDFLARE_ENABLED")
    cloudflare_api_token: str = Field(default="", env="CLOUDFLARE_API_TOKEN")
    cloudflare_zone_id: str = Field(default="", env="CLOUDFLARE_ZONE_ID")
    cloudflare_domain: str = Field(default="", env="CLOUDFLARE_DOMAIN")
    
    # Backup Configuration (optional)
    backup_enabled: bool = Field(default=False, env="BACKUP_ENABLED")
    backup_schedule: str = Field(default="0 2 * * *", env="BACKUP_SCHEDULE")
    backup_retention_days: int = Field(default=30, env="BACKUP_RETENTION_DAYS")
    backup_path: str = Field(default="/backups", env="BACKUP_PATH")
    
    # Performance Configuration (optional)
    worker_processes: int = Field(default=4, env="WORKER_PROCESSES")
    worker_threads: int = Field(default=2, env="WORKER_THREADS")
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=300, env="REQUEST_TIMEOUT")
    keep_alive_timeout: int = Field(default=5, env="KEEP_ALIVE_TIMEOUT")
    
    # Model Performance Configuration (optional)
    max_model_memory_gb: int = Field(default=16, env="MAX_MODEL_MEMORY_GB")
    model_quantization: str = Field(default="4bit", env="MODEL_QUANTIZATION")
    enable_model_caching: bool = Field(default=True, env="ENABLE_MODEL_CACHING")
    model_cache_ttl: int = Field(default=3600, env="MODEL_CACHE_TTL")
    
    # Logging Configuration (optional)
    log_file_path: str = Field(default="/app/logs/ai-api.log", env="LOG_FILE_PATH")
    log_max_size_mb: int = Field(default=100, env="LOG_MAX_SIZE_MB")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Deployment Configuration (optional)
    deployment_environment: str = Field(default="production", env="DEPLOYMENT_ENVIRONMENT")
    deployment_version: str = Field(default="1.0.0", env="DEPLOYMENT_VERSION")
    deployment_timestamp: str = Field(default="", env="DEPLOYMENT_TIMESTAMP")
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse allowed origins from string to list."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Remove brackets and split by comma
                v = v[1:-1].split(",")
                return [origin.strip().strip('"').strip("'") for origin in v]
            else:
                return [v]
        return v
    
    @validator("api_keys", pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from string to list."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                # Remove brackets and split by comma
                v = v[1:-1].split(",")
                return [key.strip().strip('"').strip("'") for key in v]
            else:
                return [v]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Changed from "forbid" to "ignore" to allow extra env vars
        protected_namespaces = ('settings_',)  # Fix Pydantic warnings about model_ fields


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global settings
    settings = Settings()
    return settings 