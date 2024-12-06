from pydantic import BaseSettings
"""
This module defines the configuration settings for the application.
Classes:
    Settings(BaseSettings): A Pydantic model that loads environment variables
                            for application configuration.
Attributes:
    settings (Settings): An instance of the Settings class that holds the
                         configuration values.
Raises:
    ValueError: If the 'database_url' environment variable is not found.
Usage:
    The configuration settings are loaded from a .env file located in the
    root directory of the project. The 'database_url' environment variable
    must be set in the .env file. If it is not set, a ValueError will be raised.
"""

class Settings(BaseSettings):
    database_url: str

    class Config:
        env_file = ".env"

settings = Settings()

if not settings.database_url:
    raise ValueError("No DATABASE_URL found in environment variables")

print(f"Database URL: {settings.database_url}")