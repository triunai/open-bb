"""
Test Configuration

Provides pytest fixtures for unit and integration tests.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ofac_scanner.infrastructure.database.models import Base


# =============================================================================
# Event Loop
# =============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session with SQLite.
    
    Uses an in-memory SQLite database for fast, isolated tests.
    """
    # Use SQLite for testing (synchronous driver works with asyncio)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with session_factory() as session:
        yield session
    
    # Cleanup
    await engine.dispose()


# =============================================================================
# Domain Fixtures
# =============================================================================

@pytest.fixture
def sample_event_data() -> dict:
    """Sample OFAC event data for testing."""
    return {
        "title": "Venezuela-related Designations; Issuance of Venezuela-related General License",
        "url": "https://ofac.treasury.gov/recent-actions/20251219",
        "published_date": "2025-12-19",
        "category": "General Licenses",
    }


@pytest.fixture
def sample_venezuela_keywords() -> list[str]:
    """Sample Venezuela keywords for testing."""
    return ["venezuela", "general license"]


@pytest.fixture
def sample_chevron_keywords() -> list[str]:
    """Sample Chevron keywords for testing."""
    return ["chevron", "oil license"]
