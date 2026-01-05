"""
Poll Run Entity

Represents a single execution of the OFAC polling job.
Used for tracking poll history, debugging, and audit trail.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class PollStatus(str, Enum):
    """Status of a poll run."""
    
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class PollRun:
    """
    Represents a single execution of the OFAC polling job.
    
    Each poll run captures:
    - When it started/completed
    - Whether it succeeded or failed
    - How many new events were discovered
    - Any error messages if it failed
    
    This provides an audit trail and helps with debugging poll issues.
    """
    
    id: UUID = field(default_factory=uuid4)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: PollStatus = PollStatus.RUNNING
    events_found: int = 0
    new_events: int = 0
    error_message: Optional[str] = None
    
    def mark_success(self, events_found: int, new_events: int) -> None:
        """Mark this poll run as successfully completed."""
        self.completed_at = datetime.utcnow()
        self.status = PollStatus.SUCCESS
        self.events_found = events_found
        self.new_events = new_events
    
    def mark_failed(self, error: str) -> None:
        """Mark this poll run as failed with an error message."""
        self.completed_at = datetime.utcnow()
        self.status = PollStatus.FAILED
        self.error_message = error
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate the duration of this poll run in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    @property
    def is_completed(self) -> bool:
        """Check if this poll run has completed (success or failure)."""
        return self.status in (PollStatus.SUCCESS, PollStatus.FAILED)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
            "events_found": self.events_found,
            "new_events": self.new_events,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
        }
