"""
Alert Entity

Represents an alert triggered by a detected OFAC event.
Alerts are used to track and notify about important events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from ofac_scanner.domain.value_objects import ConfidenceScore


class AlertType(str, Enum):
    """Types of alerts that can be triggered."""
    
    VENEZUELA_NEW = "venezuela_new"
    """New event mentioning Venezuela."""
    
    VENEZUELA_GL = "venezuela_gl"
    """New General License related to Venezuela."""
    
    POLICY_PISTOL = "policy_pistol"
    """Critical: Chevron-related event detected."""
    
    POSSIBLE_PRIVATE = "possible_private"
    """Price moved but no OFAC diff - possible private authorization."""


@dataclass
class Alert:
    """
    Represents an alert triggered by an OFAC event.
    
    Alerts provide:
    - Classification of event importance
    - Confidence scoring
    - Acknowledgment tracking for review workflow
    
    Attributes:
        id: Unique identifier
        event_id: Reference to the triggering OFAC event
        alert_type: Classification of the alert
        confidence: How confident we are this is significant
        rule_matched: Description of what triggered this alert
        triggered_at: When the alert was created
        acknowledged: Whether a human has reviewed this
        acknowledged_at: When it was acknowledged
        notes: Any notes added during review
    """
    
    event_id: UUID
    alert_type: AlertType
    confidence: ConfidenceScore
    rule_matched: str
    
    id: UUID = field(default_factory=uuid4)
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        event_id: UUID,
        alert_type: AlertType,
        confidence: float,
        rule_matched: str,
    ) -> "Alert":
        """Factory method to create a new alert."""
        return cls(
            event_id=event_id,
            alert_type=alert_type,
            confidence=ConfidenceScore(confidence),
            rule_matched=rule_matched,
        )
    
    def acknowledge(self, notes: Optional[str] = None) -> None:
        """Mark this alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.notes = notes
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical alert requiring immediate attention."""
        return self.alert_type == AlertType.POLICY_PISTOL
    
    @property
    def severity(self) -> str:
        """Get human-readable severity level."""
        if self.alert_type == AlertType.POLICY_PISTOL:
            return "critical"
        elif self.alert_type == AlertType.VENEZUELA_GL:
            return "high"
        elif self.alert_type == AlertType.VENEZUELA_NEW:
            return "medium"
        else:
            return "low"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "alert_type": self.alert_type.value,
            "severity": self.severity,
            "confidence": float(self.confidence),
            "rule_matched": self.rule_matched,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged": self.acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "notes": self.notes,
        }
