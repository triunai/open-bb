
The database configuration is managed in `src/ofac_scanner/config.py` and `src/ofac_scanner/infrastructure/database/connection.py`.

**`src/ofac_scanner/config.py` (Snippet showing database_url definition):**
```python
class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
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
    )
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure async driver is used."""
        if "postgresql://" in v and "asyncpg" not in v:
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v
```

**`src/ofac_scanner/infrastructure/database/connection.py` (Current state):**
```python
@lru_cache
def get_engine() -> AsyncEngine:
    """
    Create and cache the async database engine.
    """
    settings = get_settings()
    
    print(f"DEBUG: Connecting to DB URL: {settings.database_url}")
    
    return create_async_engine(
        settings.database_url,
        echo=settings.log_level == "DEBUG",
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections after 5 min
    )
```

**The `.env` file content (Sensitive parts redacted):**
```bash
# This file is dynamically generated. Current content (approximate):
DATABASE_URL=postgresql+asyncpg://postgres.pxni....:PASSWORD@aws-1-ap-south-1.pooler.supabase.com:5432/postgres
OFAC_API_KEY=dev
LOG_FORMAT=console
```

**What exactly fails:**
Running `python -m ofac_scanner.main` fails with `socket.gaierror: [Errno 11001] getaddrinfo failed` originating from `uvicorn/asyncpg` inside `app.py` -> `lifespan` -> `get_engine().begin()`.

**Verification of "paradox" (Ran just now):**
`python -c "import socket; print(socket.gethostbyname('aws-1-ap-south-1.pooler.supabase.com'))"` -> Returns IP `13.200.110.68`.
`nslookup aws-1-ap-south-1.pooler.supabase.com` -> Returns IP.
