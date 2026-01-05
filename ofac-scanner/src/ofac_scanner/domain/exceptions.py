"""
Domain Exceptions

Custom exceptions for domain-specific error cases.
These exceptions should be caught and translated at the
presentation layer to appropriate HTTP responses.
"""


class DomainException(Exception):
    """Base exception for all domain errors."""
    
    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__


class EventAlreadyExistsError(DomainException):
    """Raised when attempting to create a duplicate event."""
    
    def __init__(self, event_hash: str):
        super().__init__(
            f"Event with hash {event_hash[:8]}... already exists",
            code="EVENT_ALREADY_EXISTS",
        )
        self.event_hash = event_hash


class EventNotFoundError(DomainException):
    """Raised when an event cannot be found."""
    
    def __init__(self, event_id: str):
        super().__init__(
            f"Event {event_id} not found",
            code="EVENT_NOT_FOUND",
        )
        self.event_id = event_id


class PollRunNotFoundError(DomainException):
    """Raised when a poll run cannot be found."""
    
    def __init__(self, poll_run_id: str):
        super().__init__(
            f"Poll run {poll_run_id} not found",
            code="POLL_RUN_NOT_FOUND",
        )
        self.poll_run_id = poll_run_id


class ScrapingError(DomainException):
    """Raised when OFAC page scraping fails."""
    
    def __init__(self, url: str, reason: str):
        super().__init__(
            f"Failed to scrape {url}: {reason}",
            code="SCRAPING_ERROR",
        )
        self.url = url
        self.reason = reason


class ConfigurationError(DomainException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str):
        super().__init__(message, code="CONFIGURATION_ERROR")
