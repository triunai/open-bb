"""
Event Query Service

Provides read-only access to OFAC events for API endpoints.
Separates query logic from command (polling) logic.
"""

from datetime import datetime, timedelta
from typing import Optional

from ofac_scanner.domain.entities import OFACEvent
from ofac_scanner.application.interfaces import EventRepository


class EventQueryService:
    """
    Query service for OFAC events.
    
    This service provides read-only access to events for API endpoints.
    It follows CQRS principles by separating queries from commands.
    """
    
    def __init__(self, event_repository: EventRepository):
        """
        Initialize the query service.
        
        Args:
            event_repository: Event persistence
        """
        self._events = event_repository
    
    async def get_latest(self, limit: int = 20) -> list[OFACEvent]:
        """
        Get the most recent events.
        
        Args:
            limit: Maximum number of events (capped at 100)
            
        Returns:
            List of recent events
        """
        return await self._events.find_latest(min(limit, 100))
    
    async def get_venezuela_events(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        chevron_only: bool = False,
    ) -> list[OFACEvent]:
        """
        Get Venezuela-related events.
        
        Args:
            limit: Maximum number of events (capped at 200)
            since: Only events after this datetime
            chevron_only: Filter to Chevron-mentioned only
            
        Returns:
            List of Venezuela-related events
        """
        return await self._events.find_venezuela_related(
            limit=min(limit, 200),
            since=since,
            chevron_only=chevron_only,
        )
    
    async def get_diff(self, since_hours: int = 24) -> dict:
        """
        Get events detected within a time window.
        
        Args:
            since_hours: Hours to look back (capped at 168 = 1 week)
            
        Returns:
            Dict with metadata and events
        """
        hours = min(since_hours, 168)
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        events = await self._events.find_since(cutoff)
        venezuela_count = sum(1 for e in events if e.is_venezuela_related)
        
        return {
            "since": cutoff.isoformat(),
            "since_hours": hours,
            "new_count": len(events),
            "venezuela_count": venezuela_count,
            "events": events,
        }
    
    async def get_stats(self) -> dict:
        """
        Get aggregate statistics about events.
        
        Returns:
            Dict with event counts and metadata
        """
        total = await self._events.count_total()
        venezuela = await self._events.count_venezuela()
        
        return {
            "total_events": total,
            "venezuela_events": venezuela,
        }
