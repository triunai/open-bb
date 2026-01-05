"""
Alert Repository Interface

Defines the contract for persisting and querying alerts.
"""

from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from ofac_scanner.domain.entities import Alert, AlertType


class AlertRepository(ABC):
    """
    Abstract repository for alert persistence.
    
    Alerts track significant OFAC events that require attention.
    """
    
    @abstractmethod
    async def save(self, alert: Alert) -> Alert:
        """
        Persist an alert to storage.
        
        Args:
            alert: The alert to save
            
        Returns:
            The saved alert
        """
        ...
    
    @abstractmethod
    async def find_by_id(self, alert_id: UUID) -> Optional[Alert]:
        """
        Find an alert by its ID.
        
        Args:
            alert_id: The alert's unique identifier
            
        Returns:
            The alert if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def find_by_event(self, event_id: UUID) -> list[Alert]:
        """
        Find all alerts for a given event.
        
        Args:
            event_id: The event's unique identifier
            
        Returns:
            List of alerts for the event
        """
        ...
    
    @abstractmethod
    async def find_unacknowledged(
        self,
        alert_type: Optional[AlertType] = None,
        limit: int = 50,
    ) -> list[Alert]:
        """
        Find unacknowledged alerts.
        
        Args:
            alert_type: Filter by alert type (optional)
            limit: Maximum number of alerts
            
        Returns:
            List of unacknowledged alerts
        """
        ...
    
    @abstractmethod
    async def find_latest(self, limit: int = 20) -> list[Alert]:
        """
        Get the most recent alerts.
        
        Args:
            limit: Maximum number of alerts
            
        Returns:
            List of alerts ordered by triggered_at descending
        """
        ...
    
    @abstractmethod
    async def update(self, alert: Alert) -> Alert:
        """
        Update an existing alert.
        
        Args:
            alert: The alert with updated fields
            
        Returns:
            The updated alert
        """
        ...
    
    @abstractmethod
    async def count_unacknowledged(self) -> int:
        """Get count of unacknowledged alerts."""
        ...
