"""
Event Repository Interface

Defines the contract for persisting and querying OFAC events.
Infrastructure layer must implement this interface.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from ofac_scanner.domain.entities import OFACEvent
from ofac_scanner.domain.value_objects import EventHash


class EventRepository(ABC):
    """
    Abstract repository for OFAC event persistence.
    
    This interface defines the contract that any event storage
    implementation must fulfill. The application layer depends
    only on this interface, not on concrete implementations.
    """
    
    @abstractmethod
    async def save(self, event: OFACEvent) -> OFACEvent:
        """
        Persist an event to storage.
        
        If an event with the same hash already exists, this should
        update it rather than create a duplicate.
        
        Args:
            event: The event to save
            
        Returns:
            The saved event (may have updated fields like ID)
        """
        ...
    
    @abstractmethod
    async def save_many(self, events: Sequence[OFACEvent]) -> list[OFACEvent]:
        """
        Persist multiple events in a single transaction.
        
        Args:
            events: Events to save
            
        Returns:
            List of saved events
        """
        ...
    
    @abstractmethod
    async def find_by_id(self, event_id: UUID) -> Optional[OFACEvent]:
        """
        Find an event by its ID.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            The event if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def find_by_hash(self, event_hash: EventHash) -> Optional[OFACEvent]:
        """
        Find an event by its hash.
        
        Args:
            event_hash: The event's idempotency hash
            
        Returns:
            The event if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def exists_by_hash(self, event_hash: EventHash) -> bool:
        """
        Check if an event with the given hash exists.
        
        Args:
            event_hash: The hash to check
            
        Returns:
            True if an event with this hash exists
        """
        ...
    
    @abstractmethod
    async def find_latest(self, limit: int = 20) -> list[OFACEvent]:
        """
        Get the most recent events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of events ordered by first_seen_at descending
        """
        ...
    
    @abstractmethod
    async def find_venezuela_related(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        chevron_only: bool = False,
    ) -> list[OFACEvent]:
        """
        Get Venezuela-related events.
        
        Args:
            limit: Maximum number of events
            since: Only return events first seen after this time
            chevron_only: If True, only return Chevron-related events
            
        Returns:
            List of Venezuela-related events
        """
        ...
    
    @abstractmethod
    async def find_since(self, since: datetime) -> list[OFACEvent]:
        """
        Get events first seen after a given time.
        
        Args:
            since: Cutoff datetime (UTC)
            
        Returns:
            List of events first seen after the cutoff
        """
        ...
    
    @abstractmethod
    async def count_total(self) -> int:
        """Get total count of all events."""
        ...
    
    @abstractmethod
    async def count_venezuela(self) -> int:
        """Get count of Venezuela-related events."""
        ...
