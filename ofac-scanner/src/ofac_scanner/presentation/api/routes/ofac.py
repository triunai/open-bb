"""
OFAC Event Routes

API endpoints for OFAC event queries.
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from ofac_scanner.application.services import EventQueryService, PollingService
from ofac_scanner.presentation.api.dependencies import (
    verify_api_key,
    get_event_query_service,
    get_polling_service,
)
from ofac_scanner.presentation.api.state import get_scheduler


router = APIRouter(
    prefix="/ofac",
    tags=["OFAC"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/latest")
async def get_latest_events(
    limit: int = Query(default=20, ge=1, le=100),
    query_service: EventQueryService = Depends(get_event_query_service),
) -> list[dict[str, Any]]:
    """
    Get the most recent OFAC events.
    
    Args:
        limit: Maximum number of events to return (1-100)
        
    Returns:
        List of recent events
    """
    events = await query_service.get_latest(limit=limit)
    return [e.to_dict() for e in events]


@router.get("/venezuela")
async def get_venezuela_events(
    limit: int = Query(default=50, ge=1, le=200),
    chevron_only: bool = Query(default=False),
    query_service: EventQueryService = Depends(get_event_query_service),
) -> list[dict[str, Any]]:
    """
    Get Venezuela-related OFAC events.
    
    Args:
        limit: Maximum number of events (1-200)
        chevron_only: Filter to Chevron-mentioned events only
        
    Returns:
        List of Venezuela-related events
    """
    events = await query_service.get_venezuela_events(
        limit=limit,
        chevron_only=chevron_only,
    )
    return [e.to_dict() for e in events]


@router.get("/diff")
async def get_diff(
    since_hours: int = Query(default=24, ge=1, le=168),
    query_service: EventQueryService = Depends(get_event_query_service),
) -> dict[str, Any]:
    """
    Get events detected within a time window.
    
    Args:
        since_hours: Hours to look back (1-168, i.e., up to 1 week)
        
    Returns:
        Dict with metadata and events
    """
    result = await query_service.get_diff(since_hours=since_hours)
    return {
        "since": result["since"],
        "since_hours": result["since_hours"],
        "new_count": result["new_count"],
        "venezuela_count": result["venezuela_count"],
        "events": [e.to_dict() for e in result["events"]],
    }


@router.get("/status")
async def get_status(
    query_service: EventQueryService = Depends(get_event_query_service),
) -> str:
    """
    Get scanner status formatted for markdown widget.
    
    Returns:
        Markdown-formatted status string
    """
    scheduler = get_scheduler()
    stats = await query_service.get_stats()
    
    # Get last Venezuela event
    venezuela_events = await query_service.get_venezuela_events(limit=1)
    last_vz = venezuela_events[0] if venezuela_events else None
    
    # Build markdown status
    lines = [
        "## 🔍 OFAC Scanner Status",
        "",
        f"**Total Events:** {stats['total_events']}",
        f"**Venezuela Events:** {stats['venezuela_events']}",
        "",
    ]
    
    if scheduler and scheduler.is_running:
        lines.append("**Scheduler:** ✅ Running")
        if scheduler.next_run_time:
            lines.append(f"**Next Poll:** {scheduler.next_run_time.strftime('%Y-%m-%d %H:%M UTC')}")
    else:
        lines.append("**Scheduler:** ⚠️ Stopped")
    
    lines.append("")
    
    if last_vz:
        lines.extend([
            "### Last Venezuela Event",
            f"**Date:** {last_vz.published_date}",
            f"**Title:** {last_vz.title[:80]}{'...' if len(last_vz.title) > 80 else ''}",
        ])
    
    return "\n".join(lines)


@router.post("/poll")
async def trigger_poll(
    polling_service: PollingService = Depends(get_polling_service),
) -> dict[str, Any]:
    """
    Manually trigger an immediate poll.
    
    Returns:
        Poll run results
    """
    poll_run = await polling_service.poll()
    return poll_run.to_dict()
