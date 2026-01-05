"""
Application State

Global state management for the application.
Separated from app.py to avoid circular imports.
"""

from ofac_scanner.infrastructure.scheduler import PollingScheduler


# Global scheduler instance (managed by app lifespan)
_scheduler: PollingScheduler | None = None


def get_scheduler() -> PollingScheduler | None:
    """Get the global scheduler instance."""
    return _scheduler


def set_scheduler(scheduler: PollingScheduler | None) -> None:
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler
