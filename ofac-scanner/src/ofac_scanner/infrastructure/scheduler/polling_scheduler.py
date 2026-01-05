"""
Polling Scheduler

Manages the background polling job using APScheduler.
"""

import asyncio
from typing import Callable, Awaitable

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ofac_scanner.config import get_settings


logger = structlog.get_logger(__name__)


class PollingScheduler:
    """
    Manages the background OFAC polling job.
    
    Uses APScheduler's AsyncIOScheduler to run the polling
    service at configured intervals.
    """
    
    def __init__(self):
        """Initialize the scheduler."""
        self._scheduler = AsyncIOScheduler(
            job_defaults={
                "coalesce": True,  # Combine missed runs
                "max_instances": 1,  # Only one poll at a time
                "misfire_grace_time": 300,  # 5 min grace for misfires
            }
        )
        self._poll_job_id = "ofac_poll"
    
    def add_poll_job(
        self,
        poll_func: Callable[[], Awaitable[None]],
        interval_minutes: int | None = None,
    ) -> None:
        """
        Add the polling job to the scheduler.
        
        Args:
            poll_func: Async function to call for polling
            interval_minutes: Polling interval (default from settings)
        """
        settings = get_settings()
        interval = interval_minutes or settings.poll_interval_minutes
        
        # Create wrapper to handle errors gracefully
        async def wrapped_poll():
            try:
                await poll_func()
            except Exception as e:
                logger.error(
                    "Poll job failed",
                    error=str(e),
                    exc_info=True,
                )
        
        self._scheduler.add_job(
            wrapped_poll,
            trigger=IntervalTrigger(minutes=interval),
            id=self._poll_job_id,
            name="OFAC Polling Job",
            replace_existing=True,
        )
        
        logger.info(
            "Poll job scheduled",
            interval_minutes=interval,
        )
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler gracefully."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")
    
    def trigger_now(self) -> None:
        """Trigger an immediate poll run."""
        job = self._scheduler.get_job(self._poll_job_id)
        if job:
            job.modify(next_run_time=None)  # Run immediately
            logger.info("Triggered immediate poll")
    
    @property
    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._scheduler.running
    
    @property
    def next_run_time(self):
        """Get the next scheduled run time."""
        job = self._scheduler.get_job(self._poll_job_id)
        return job.next_run_time if job else None
