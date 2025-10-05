"""
Application configuration settings

This module defines the application configuration using Pydantic Settings.
Settings can be overridden via environment variables or .env file.

Environment Variables:
    PROJECT_NAME: Name of the project (default: "FastAPI Bee")
    VERSION: API version (default: "0.1.0")
    API_V1_STR: API v1 prefix (default: "/api/v1")
    ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins

Example .env file:
    PROJECT_NAME="My API"
    VERSION="1.0.0"
    ALLOWED_ORIGINS="http://localhost:3000,https://example.com"
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings

    Pydantic Settings model that loads configuration from environment
    variables or .env file. All settings are validated and type-checked.

    Attributes:
        PROJECT_NAME (str): The name of the project/API
        VERSION (str): Current version of the API
        API_V1_STR (str): URL prefix for API v1 endpoints
        ALLOWED_ORIGINS (List[str]): List of allowed CORS origins

    Configuration:
        - Reads from .env file if present
        - Case-sensitive environment variable names
        - Allows extra environment variables

    Placeholders for future features:
        - DATABASE_URL: Database connection string
        - SECRET_KEY: JWT secret key for authentication
        - ALGORITHM: JWT algorithm
        - ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time
    """

    PROJECT_NAME: str = "FastAPI Bee"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Database (placeholder for future use)
    # DATABASE_URL: str = "sqlite:///./app.db"

    # Security (placeholder for future use)
    # SECRET_KEY: str = "your-secret-key-here"
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )


# Global settings instance
# This is a singleton that should be imported and used throughout the application
settings = Settings()

