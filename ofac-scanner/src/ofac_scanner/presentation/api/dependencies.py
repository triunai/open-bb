"""
FastAPI Dependencies

Provides dependency injection for routes using FastAPI's Depends system.
This keeps routes clean and enables easy testing via dependency overrides.
"""

from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ofac_scanner.config import get_settings, Settings
from ofac_scanner.infrastructure.database import get_session
from ofac_scanner.infrastructure.database.repositories import (
    SQLEventRepository,
    SQLPollRunRepository,
    SQLAlertRepository,
)
from ofac_scanner.infrastructure.scrapers import HTTPOFACScraper
from ofac_scanner.application.interfaces import (
    EventRepository,
    PollRunRepository,
    AlertRepository,
    OFACScraper,
)
from ofac_scanner.application.services import (
    PollingService,
    EventQueryService,
    AlertService,
    KeywordMatcher,
)


# =============================================================================
# Configuration
# =============================================================================

def get_config() -> Settings:
    """Get application settings."""
    return get_settings()


# =============================================================================
# Authentication
# =============================================================================

async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-KEY"),
    settings: Settings = Depends(get_config),
) -> None:
    """
    Verify API key from request header.
    
    If no API key is configured (dev mode), auth is bypassed.
    
    Raises:
        HTTPException: If API key is invalid
    """
    if settings.ofac_api_key is None:
        # Dev mode: no auth required
        return
    
    if x_api_key != settings.ofac_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "X-API-KEY"},
        )


# =============================================================================
# Database Session
# =============================================================================

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for request."""
    async for session in get_session():
        yield session


# =============================================================================
# Repositories
# =============================================================================

async def get_event_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EventRepository:
    """Get event repository instance."""
    return SQLEventRepository(session)


async def get_poll_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PollRunRepository:
    """Get poll run repository instance."""
    return SQLPollRunRepository(session)


async def get_alert_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AlertRepository:
    """Get alert repository instance."""
    return SQLAlertRepository(session)


# =============================================================================
# Infrastructure
# =============================================================================

def get_scraper() -> OFACScraper:
    """Get OFAC scraper instance."""
    return HTTPOFACScraper()


def get_keyword_matcher() -> KeywordMatcher:
    """Get keyword matcher instance."""
    return KeywordMatcher()


# =============================================================================
# Application Services
# =============================================================================

async def get_event_query_service(
    event_repo: EventRepository = Depends(get_event_repository),
) -> EventQueryService:
    """Get event query service instance."""
    return EventQueryService(event_repo)


async def get_alert_service(
    alert_repo: AlertRepository = Depends(get_alert_repository),
    matcher: KeywordMatcher = Depends(get_keyword_matcher),
) -> AlertService:
    """Get alert service instance."""
    return AlertService(alert_repo, matcher)


async def get_polling_service(
    scraper: OFACScraper = Depends(get_scraper),
    event_repo: EventRepository = Depends(get_event_repository),
    poll_repo: PollRunRepository = Depends(get_poll_repository),
    alert_service: AlertService = Depends(get_alert_service),
    matcher: KeywordMatcher = Depends(get_keyword_matcher),
) -> PollingService:
    """Get polling service instance."""
    return PollingService(
        scraper=scraper,
        event_repository=event_repo,
        poll_repository=poll_repo,
        alert_service=alert_service,
        keyword_matcher=matcher,
    )
