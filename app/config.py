#!/usr/bin/env python3
"""
Configuration management for AI Code Evaluator
Handles environment variables, logging setup, and production settings
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    app_name: str = Field(default="AI Code Evaluator", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    
    # File upload settings
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=100 * 1024 * 1024, env="MAX_FILE_SIZE")  # 100MB
    allowed_extensions: list = Field(default=[".ipynb", ".py", ".sql", ".zip"], env="ALLOWED_EXTENSIONS")
    
    # Database settings (for future use)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # AI Model settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/app.log", env="LOG_FILE")
    log_max_size: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_SIZE")  # 10MB
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Security settings
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    # Evaluation settings
    evaluation_timeout: int = Field(default=300, env="EVALUATION_TIMEOUT")  # 5 minutes
    max_concurrent_evaluations: int = Field(default=5, env="MAX_CONCURRENT_EVALUATIONS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def setup_logging() -> None:
    """Setup application logging with rotation and formatting."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.log_level}, File: {settings.log_file}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

def validate_settings() -> None:
    """Validate critical settings and create necessary directories."""
    
    # Create upload directory
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    
    # Validate file size
    if settings.max_file_size <= 0:
        raise ValueError("MAX_FILE_SIZE must be positive")
    
    # Validate timeout
    if settings.evaluation_timeout <= 0:
        raise ValueError("EVALUATION_TIMEOUT must be positive")
    
    # Validate concurrent evaluations
    if settings.max_concurrent_evaluations <= 0:
        raise ValueError("MAX_CONCURRENT_EVALUATIONS must be positive")
    
    logger = get_logger(__name__)
    logger.info(f"Settings validated - Upload dir: {upload_path}, Max file size: {settings.max_file_size}")

# Initialize logging when module is imported
setup_logging() 