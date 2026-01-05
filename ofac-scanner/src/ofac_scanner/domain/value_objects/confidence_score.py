"""
Confidence Score Value Object

Represents a confidence level between 0.0 and 1.0, used for
alert and event scoring.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    """
    Immutable confidence score between 0.0 and 1.0.
    
    Used to express how confident we are about an alert or
    event's significance.
    
    Attributes:
        value: The confidence value (0.0 to 1.0)
    """
    
    value: float
    
    def __post_init__(self) -> None:
        """Validate the confidence value is in valid range."""
        # Use object.__setattr__ because dataclass is frozen
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.value}")
    
    @classmethod
    def high(cls) -> "ConfidenceScore":
        """Create a high confidence score (0.9)."""
        return cls(0.9)
    
    @classmethod
    def medium(cls) -> "ConfidenceScore":
        """Create a medium confidence score (0.6)."""
        return cls(0.6)
    
    @classmethod
    def low(cls) -> "ConfidenceScore":
        """Create a low confidence score (0.3)."""
        return cls(0.3)
    
    @classmethod
    def zero(cls) -> "ConfidenceScore":
        """Create a zero confidence score."""
        return cls(0.0)
    
    def __float__(self) -> float:
        """Allow conversion to float."""
        return self.value
    
    def __str__(self) -> str:
        """Return as percentage string."""
        return f"{self.value:.0%}"
    
    def __lt__(self, other: object) -> bool:
        """Compare confidence scores."""
        if isinstance(other, ConfidenceScore):
            return self.value < other.value
        if isinstance(other, (int, float)):
            return self.value < other
        return NotImplemented
    
    def __le__(self, other: object) -> bool:
        """Compare confidence scores."""
        if isinstance(other, ConfidenceScore):
            return self.value <= other.value
        if isinstance(other, (int, float)):
            return self.value <= other
        return NotImplemented
    
    def __gt__(self, other: object) -> bool:
        """Compare confidence scores."""
        if isinstance(other, ConfidenceScore):
            return self.value > other.value
        if isinstance(other, (int, float)):
            return self.value > other
        return NotImplemented
    
    def __ge__(self, other: object) -> bool:
        """Compare confidence scores."""
        if isinstance(other, ConfidenceScore):
            return self.value >= other.value
        if isinstance(other, (int, float)):
            return self.value >= other
        return NotImplemented
    
    @property
    def label(self) -> Literal["critical", "high", "medium", "low"]:
        """Get a human-readable label for the confidence level."""
        if self.value >= 0.9:
            return "critical"
        elif self.value >= 0.7:
            return "high"
        elif self.value >= 0.4:
            return "medium"
        else:
            return "low"
    
    def add(self, amount: float) -> "ConfidenceScore":
        """Add to the confidence score, clamping to [0, 1]."""
        new_value = max(0.0, min(1.0, self.value + amount))
        return ConfidenceScore(new_value)
