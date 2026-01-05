"""
Database Connection Management

Provides async SQLAlchemy engine and session factory.
Uses connection pooling for production workloads.
"""

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ofac_scanner.config import get_settings



# @lru_cache  # TEMPORARILY DISABLED for debugging

def get_engine() -> AsyncEngine:
    """
    Create and cache the async database engine.
    
    Uses connection pooling with sensible defaults for
    a background polling service.
    
    Returns:
        Async SQLAlchemy engine
    """
    settings = get_settings()
    
    import socket
    from sqlalchemy.engine.url import make_url

    url = make_url(settings.database_url)
    
    # ==========================================================================
    # WORKAROUND: Hardcoded IP for Windows + asyncio + Uvicorn DNS bug
    # ==========================================================================
    # Root Cause: socket.gethostbyname() fails with [Errno 11001] getaddrinfo
    # inside the Uvicorn worker process, but works in standalone Python scripts.
    # This is a Windows-specific asyncio event loop interaction issue.
    #
    # Evidence:
    # - alembic upgrade head (migrations) work fine
    # - standalone debug_psycopg.py connects successfully
    # - socket.gethostbyname() works in regular Python scripts
    # - BUT fails inside FastAPI/Uvicorn process context
    #
    # Long-term fix: Investigate Uvicorn worker process DNS resolver context
    # Alternative: Pin IP in C:\Windows\System32\drivers\etc\hosts
    # ==========================================================================
    
    # Debug: Print the parsed URL details
    print(f"DEBUG: Parsed URL - host={url.host}, port={url.port}, database={url.database}")
    
    SUPABASE_POOLER_HOST = "aws-1-ap-south-1.pooler.supabase.com"
    SUPABASE_POOLER_IP = "13.200.110.68"  # Pre-resolved IP (may change!)
    
    if url.host == SUPABASE_POOLER_HOST:
        ip = SUPABASE_POOLER_IP
        print(f"DEBUG: Using hardcoded IP for {url.host} -> {ip} (Windows DNS workaround)")
    else:
        # Try normal DNS resolution for other hosts
        try:
            ip = socket.gethostbyname(url.host)
            print(f"DEBUG: Resolved {url.host} -> {ip}")
        except Exception as e:
            print(f"DEBUG: DNS failed ({e}), using host as-is")
            ip = url.host

    # ==========================================================================
    # Use asyncpg driver (NOT psycopg3)
    # ==========================================================================
    # psycopg3 requires SelectorEventLoop on Windows, but Uvicorn uses
    # ProactorEventLoop by default and the WindowsSelectorEventLoopPolicy
    # set in main.py doesn't propagate to the worker process.
    # asyncpg works with ProactorEventLoop, so we use it instead.
    # ==========================================================================
    url = url.set(drivername="postgresql+asyncpg")
    
    # For asyncpg, we need to modify the URL directly with the IP
    # since asyncpg doesn't support "hostaddr" connect_arg like psycopg
    # Instead, we replace the host in the URL with the resolved IP
    url = url.set(host=ip)
    
    # Render string for debugging
    print(f"DEBUG: Connecting to DB Driver: {url.drivername}")
    print(f"DEBUG: Connecting to DB URL: {url.render_as_string(hide_password=True)}")
    
    return create_async_engine(
        url,
        echo=settings.log_level == "DEBUG",
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "ssl": "require",  # asyncpg uses 'ssl' instead of 'sslmode'
        }
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Create and cache the session factory.
    
    Returns:
        Async session maker configured for the engine
    """
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that yields database sessions.
    
    Usage with FastAPI:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...
    
    Yields:
        AsyncSession that will be closed after use
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
