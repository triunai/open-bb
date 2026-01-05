"""Application layer interfaces (ports)."""

from ofac_scanner.application.interfaces.event_repository import EventRepository
from ofac_scanner.application.interfaces.poll_repository import PollRunRepository
from ofac_scanner.application.interfaces.alert_repository import AlertRepository
from ofac_scanner.application.interfaces.scraper import OFACScraper

__all__ = [
    "EventRepository",
    "PollRunRepository",
    "AlertRepository",
    "OFACScraper",
]
