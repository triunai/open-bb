"""
Event Hash Value Object

Provides a stable, deterministic hash for OFAC events to enable
idempotent event processing. Two events with the same hash are
considered the same event.
"""

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Optional


@dataclass(frozen=True, slots=True)
class EventHash:
    """
    Immutable hash value for OFAC event deduplication.
    
    The hash is computed from:
    - Event title
    - Event URL
    - Published date (if available)
    
    This ensures that the same event won't be processed twice,
    even if we poll the OFAC page multiple times.
    
    Attributes:
        value: The SHA-256 hash as a hexadecimal string
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate the hash value."""
        if not self.value:
            raise ValueError("EventHash value cannot be empty")
        if len(self.value) != 64:
            raise ValueError("EventHash must be a 64-character SHA-256 hex string")
        if not all(c in "0123456789abcdef" for c in self.value.lower()):
            raise ValueError("EventHash must contain only hexadecimal characters")
    
    @classmethod
    def compute(
        cls,
        title: str,
        url: str,
        published_date: Optional[date] = None,
    ) -> "EventHash":
        """
        Compute a stable hash from event properties.
        
        Args:
            title: Event title
            url: Event URL
            published_date: Event publication date (optional)
        
        Returns:
            An EventHash instance with the computed SHA-256 hash
        """
        date_str = published_date.isoformat() if published_date else "unknown"
        
        # Normalize inputs for consistent hashing
        normalized_title = title.strip().lower()
        normalized_url = url.strip().lower()
        
        content = f"{normalized_title}|{normalized_url}|{date_str}"
        hash_value = sha256(content.encode("utf-8")).hexdigest()
        
        return cls(value=hash_value)
    
    def __str__(self) -> str:
        """Return the hash value as a string."""
        return self.value
    
    def __eq__(self, other: object) -> bool:
        """Compare two EventHash instances."""
        if isinstance(other, EventHash):
            return self.value.lower() == other.value.lower()
        if isinstance(other, str):
            return self.value.lower() == other.lower()
        return NotImplemented
    
    def __hash__(self) -> int:
        """Allow use in sets and as dict keys."""
        return hash(self.value.lower())
    
    @property
    def short(self) -> str:
        """Return a shortened version for display (first 8 chars)."""
        return self.value[:8]
