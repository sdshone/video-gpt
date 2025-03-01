from pydantic_settings import BaseSettings
from typing import Optional
import logging
from functools import lru_cache
from dotenv import load_dotenv
import os

# Load .env file explicitly
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    # API settings
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    API_RATE_LIMIT: str = "5/minute"
    API_TIMEOUT: int = 30

    # JWT settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis settings
    REDIS_BROKER: str = "redis://localhost:6379/0"
    REDIS_BACKEND: str = "redis://localhost:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 