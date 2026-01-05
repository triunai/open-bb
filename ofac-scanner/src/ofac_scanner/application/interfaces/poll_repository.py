"""
Poll Run Repository Interface

Defines the contract for persisting and querying poll run records.
"""

from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from ofac_scanner.domain.entities import PollRun


class PollRunRepository(ABC):
    """
    Abstract repository for poll run persistence.
    
    Poll runs track the execution history of the OFAC polling job,
    providing an audit trail and debugging information.
    """
    
    @abstractmethod
    async def save(self, poll_run: PollRun) -> PollRun:
        """
        Persist a poll run to storage.
        
        Args:
            poll_run: The poll run to save
            
        Returns:
            The saved poll run
        """
        ...
    
    @abstractmethod
    async def find_by_id(self, poll_run_id: UUID) -> Optional[PollRun]:
        """
        Find a poll run by its ID.
        
        Args:
            poll_run_id: The poll run's unique identifier
            
        Returns:
            The poll run if found, None otherwise
        """
        ...
    
    @abstractmethod
    async def find_latest(self, limit: int = 10) -> list[PollRun]:
        """
        Get the most recent poll runs.
        
        Args:
            limit: Maximum number of poll runs to return
            
        Returns:
            List of poll runs ordered by started_at descending
        """
        ...
    
    @abstractmethod
    async def find_last_successful(self) -> Optional[PollRun]:
        """
        Get the most recent successful poll run.
        
        Returns:
            The last successful poll run, or None if none exist
        """
        ...
    
    @abstractmethod
    async def update(self, poll_run: PollRun) -> PollRun:
        """
        Update an existing poll run.
        
        Args:
            poll_run: The poll run with updated fields
            
        Returns:
            The updated poll run
        """
        ...
