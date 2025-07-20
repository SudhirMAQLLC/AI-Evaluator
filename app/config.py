from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./assignment_evaluator.db"
    
    # File upload
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list = [".zip", ".ipynb", ".sql", ".csv", ".py"]
    
    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379"
    
    # Snowflake connection (for validation)
    snowflake_account: Optional[str] = None
    snowflake_user: Optional[str] = None
    snowflake_password: Optional[str] = None
    snowflake_warehouse: Optional[str] = None
    snowflake_database: Optional[str] = None
    snowflake_schema: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Evaluation settings
    max_evaluation_time: int = 300  # 5 minutes
    auto_delete_uploads: bool = True
    delete_after_hours: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()

# Create upload directory if it doesn't exist
os.makedirs(settings.upload_dir, exist_ok=True) 