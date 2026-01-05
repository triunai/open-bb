"""Domain value objects - immutable typed values."""

from ofac_scanner.domain.value_objects.event_hash import EventHash
from ofac_scanner.domain.value_objects.confidence_score import ConfidenceScore

__all__ = [
    "EventHash",
    "ConfidenceScore",
]
