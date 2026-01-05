"""
Configuration management using Pydantic Settings.

This module provides a single source of truth for all configuration values,
loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Usage:
        settings = get_settings()
        print(settings.database_url)
    """
    
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://ofac:ofac@localhost:5432/ofac",
        description="PostgreSQL connection string (async driver)",
        validation_alias="DATABASE_URL",  # Explicit alias for clarity
    )
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure async driver is used and strip CRLF/whitespace."""
        # CRITICAL: Strip hidden \r\n from Windows-generated .env files
        v = v.strip()
        if "postgresql://" in v and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v
    
    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    ofac_api_key: str | None = Field(
        default=None,
        description="API key for authentication. If None or empty, auth is disabled (dev mode).",
    )
    
    @field_validator("ofac_api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v: str | None) -> str | None:
        """Treat empty strings as None (dev mode)."""
        if v is None or (isinstance(v, str) and v.strip() == ""):
            return None
        return v
    
    cors_origins: list[str] = Field(
        default=[
            "https://pro.openbb.co",
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed CORS origins",
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # -------------------------------------------------------------------------
    # Polling
    # -------------------------------------------------------------------------
    poll_interval_minutes: int = Field(
        default=15,
        ge=5,
        le=1440,
        description="How often to poll OFAC pages (minutes)",
    )
    
    poll_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts on poll failure",
    )
    
    enable_scheduler: bool = Field(
        default=True,
        description="Enable/disable the background polling scheduler",
    )
    
    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    
    log_format: Literal["json", "console"] = Field(
        default="json",
        description="Log output format",
    )
    
    # -------------------------------------------------------------------------
    # Server
    # -------------------------------------------------------------------------
    host: str = Field(
        default="0.0.0.0",
        description="Server bind host",
    )
    
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server bind port",
    )
    
    reload: bool = Field(
        default=False,
        description="Enable auto-reload (development only)",
    )
    
    # -------------------------------------------------------------------------
    # OFAC Scraping
    # -------------------------------------------------------------------------
    ofac_base_url: str = Field(
        default="https://ofac.treasury.gov",
        description="OFAC website base URL",
    )
    
    request_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="HTTP request timeout",
    )
    
    # -------------------------------------------------------------------------
    # Derived Properties
    # -------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        """Check if running in development mode (no API key)."""
        return self.ofac_api_key is None
    
    @property
    def ofac_recent_actions_url(self) -> str:
        """Full URL for OFAC Recent Actions page."""
        return f"{self.ofac_base_url}/recent-actions"


# @lru_cache  # TEMPORARILY DISABLED for debugging .env loading
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns a singleton Settings object, loaded once from environment.
    """
    import os
    from pathlib import Path
    
    # =========================================================================
    # DEBUG: Diagnose .env loading issues
    # =========================================================================
    print(f"DEBUG CONFIG: CWD = {os.getcwd()}")
    print(f"DEBUG CONFIG: .env exists in CWD? {Path('.env').exists()}")
    print(f"DEBUG CONFIG: ../.env exists? {Path('../.env').exists()}")
    raw_db_url = os.environ.get('DATABASE_URL')
    print(f"DEBUG CONFIG: os.environ DATABASE_URL repr = {repr(raw_db_url)}")
    # =========================================================================
    
    settings = Settings()
    
    # Debug: Show what Pydantic actually loaded
    print(f"DEBUG CONFIG: Pydantic loaded database_url repr = {repr(settings.database_url)}")
    
    return settings
