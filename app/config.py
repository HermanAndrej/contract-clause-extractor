"""Application configuration."""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "sqlite:///./contracts.db"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Fast and cost-effective for clause extraction
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.1  # Lower temperature for more consistent extraction
    
    # Application
    app_name: str = "Contract Clause Extractor"
    app_version: str = "1.0.0"
    
    # File upload
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

