"""
OFAC Event Entity

Represents a single action/update from the OFAC Recent Actions page.
This is the core domain object that the system revolves around.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from ofac_scanner.domain.value_objects import EventHash


@dataclass
class OFACEvent:
    """
    Represents a single OFAC action or update.
    
    This entity is the core of the OFAC scanning system. Each event
    represents one item from the OFAC Recent Actions page.
    
    Attributes:
        id: Unique identifier (UUID)
        event_hash: Idempotency key derived from title+url+date
        title: Event title as displayed on OFAC page
        url: Full URL to the event detail page
        published_date: Date the event was published (if available)
        category: Event category (e.g., "Sanctions List Updates")
        is_venezuela_related: Whether keywords indicate Venezuela relevance
        is_chevron_related: Whether keywords indicate Chevron relevance
        keywords_matched: List of matched keywords
        first_seen_at: When our scanner first detected this event
        poll_run_id: ID of the poll run that discovered this event
    """
    
    # Required fields
    title: str
    url: str
    event_hash: EventHash
    
    # Optional fields with defaults
    id: UUID = field(default_factory=uuid4)
    published_date: Optional[date] = None
    category: Optional[str] = None
    is_venezuela_related: bool = False
    is_chevron_related: bool = False
    keywords_matched: list[str] = field(default_factory=list)
    first_seen_at: datetime = field(default_factory=datetime.utcnow)
    poll_run_id: Optional[UUID] = None
    
    def __post_init__(self) -> None:
        """Validate invariants after initialization."""
        if not self.title.strip():
            raise ValueError("Event title cannot be empty")
        if not self.url.strip():
            raise ValueError("Event URL cannot be empty")
    
    @classmethod
    def create(
        cls,
        title: str,
        url: str,
        published_date: Optional[date] = None,
        category: Optional[str] = None,
        poll_run_id: Optional[UUID] = None,
    ) -> "OFACEvent":
        """
        Factory method to create a new OFAC event.
        
        Automatically computes the event hash for idempotency.
        """
        event_hash = EventHash.compute(title, url, published_date)
        return cls(
            title=title.strip(),
            url=url.strip(),
            event_hash=event_hash,
            published_date=published_date,
            category=category,
            poll_run_id=poll_run_id,
        )
    
    def mark_venezuela_related(self, keywords: list[str]) -> None:
        """Mark this event as Venezuela-related with matched keywords."""
        self.is_venezuela_related = True
        self.keywords_matched.extend(keywords)
    
    def mark_chevron_related(self, keywords: list[str]) -> None:
        """Mark this event as Chevron-related with matched keywords."""
        self.is_chevron_related = True
        self.keywords_matched.extend(keywords)
    
    @property
    def is_policy_pistol(self) -> bool:
        """
        Check if this event represents a "policy pistol" signal.
        
        A policy pistol is when both Venezuela AND Chevron are mentioned,
        indicating potential direct impact on the CVX thesis.
        """
        return self.is_venezuela_related and self.is_chevron_related
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "event_hash": str(self.event_hash),
            "title": self.title,
            "url": self.url,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "category": self.category,
            "is_venezuela_related": self.is_venezuela_related,
            "is_chevron_related": self.is_chevron_related,
            "keywords_matched": self.keywords_matched,
            "first_seen_at": self.first_seen_at.isoformat(),
        }
