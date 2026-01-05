"""
Health Check Routes

Provides health check endpoints for monitoring and debugging.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from ofac_scanner import __version__
from ofac_scanner.application.services import EventQueryService
from ofac_scanner.presentation.api.dependencies import get_event_query_service
from ofac_scanner.presentation.api.state import get_scheduler


router = APIRouter(tags=["Health"])


@router.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint with basic service info.
    
    Returns:
        Service name and version
    """
    return {
        "service": "OFAC Scanner",
        "version": __version__,
    }


@router.get("/health")
async def health_check(
    query_service: EventQueryService = Depends(get_event_query_service),
) -> dict[str, Any]:
    """
    Health check endpoint with service status.
    
    Returns:
        Health status including scheduler and database info
    """
    scheduler = get_scheduler()
    stats = await query_service.get_stats()
    
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.utcnow().isoformat(),
        "scheduler": {
            "running": scheduler.is_running if scheduler else False,
            "next_run": scheduler.next_run_time.isoformat() if scheduler and scheduler.next_run_time else None,
        },
        "database": {
            "total_events": stats["total_events"],
            "venezuela_events": stats["venezuela_events"],
        },
    }
