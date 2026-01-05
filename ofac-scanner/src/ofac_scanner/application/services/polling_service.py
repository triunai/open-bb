"""
Polling Service

Orchestrates the OFAC polling workflow:
1. Fetch OFAC pages
2. Extract events
3. Deduplicate against existing events
4. Tag Venezuela/Chevron related
5. Trigger alerts for significant events
"""

import structlog
from datetime import datetime
from typing import Optional

from ofac_scanner.domain.entities import OFACEvent, PollRun
from ofac_scanner.domain.value_objects import EventHash
from ofac_scanner.application.interfaces import (
    EventRepository,
    PollRunRepository,
    OFACScraper,
)
from ofac_scanner.application.services.keyword_matcher import KeywordMatcher
from ofac_scanner.application.services.alert_service import AlertService


logger = structlog.get_logger(__name__)


class PollingService:
    """
    Orchestrates the OFAC polling workflow.
    
    This service is the main entry point for the polling job.
    It coordinates between the scraper, repositories, and alert service.
    """
    
    def __init__(
        self,
        scraper: OFACScraper,
        event_repository: EventRepository,
        poll_repository: PollRunRepository,
        alert_service: AlertService,
        keyword_matcher: Optional[KeywordMatcher] = None,
    ):
        """
        Initialize the polling service.
        
        Args:
            scraper: OFAC page scraper implementation
            event_repository: Event persistence
            poll_repository: Poll run persistence
            alert_service: Alert handling
            keyword_matcher: Keyword matching (optional, uses default)
        """
        self._scraper = scraper
        self._events = event_repository
        self._polls = poll_repository
        self._alerts = alert_service
        self._matcher = keyword_matcher or KeywordMatcher()
    
    async def poll(self) -> PollRun:
        """
        Execute a complete polling cycle.
        
        This is the main entry point called by the scheduler.
        
        Returns:
            PollRun with the results of this poll cycle
        """
        # Create poll run record
        poll_run = PollRun()
        await self._polls.save(poll_run)
        
        log = logger.bind(poll_run_id=str(poll_run.id))
        log.info("Starting OFAC poll")
        
        try:
            # Step 1: Fetch OFAC Recent Actions page
            result = await self._scraper.scrape_recent_actions()
            
            if not result.success:
                raise Exception(result.error or "Scraping failed")
            
            log.info(
                "Scraped OFAC page",
                events_found=len(result.events),
                url=result.url,
            )
            
            # Step 2: Convert to domain entities
            events = [
                OFACEvent.create(
                    title=e.title,
                    url=e.url,
                    published_date=e.published_date,
                    category=e.category,
                    poll_run_id=poll_run.id,
                )
                for e in result.events
            ]
            
            # Step 3: Filter out existing events (deduplication)
            new_events: list[OFACEvent] = []
            for event in events:
                exists = await self._events.exists_by_hash(event.event_hash)
                if not exists:
                    new_events.append(event)
            
            log.info(
                "Deduplication complete",
                total_events=len(events),
                new_events=len(new_events),
            )
            
            # Step 4: Tag Venezuela/Chevron related
            for event in new_events:
                self._tag_event(event)
            
            # Step 5: Persist new events
            if new_events:
                await self._events.save_many(new_events)
            
            # Step 6: Trigger alerts for significant events
            for event in new_events:
                await self._alerts.evaluate_and_alert(event)
            
            # Mark poll as successful
            poll_run.mark_success(
                events_found=len(events),
                new_events=len(new_events),
            )
            await self._polls.update(poll_run)
            
            log.info(
                "Poll completed successfully",
                new_events=len(new_events),
                duration_seconds=poll_run.duration_seconds,
            )
            
            return poll_run
            
        except Exception as e:
            # Mark poll as failed
            poll_run.mark_failed(str(e))
            await self._polls.update(poll_run)
            
            log.error(
                "Poll failed",
                error=str(e),
                duration_seconds=poll_run.duration_seconds,
            )
            
            raise
    
    def _tag_event(self, event: OFACEvent) -> None:
        """
        Tag an event with Venezuela/Chevron flags.
        
        Args:
            event: Event to tag (modified in place)
        """
        search_text = self._matcher.compute_search_text(
            event.title,
            event.category,
        )
        
        # Check Venezuela
        venezuela_result = self._matcher.match_venezuela(search_text)
        if venezuela_result.is_match:
            event.mark_venezuela_related(venezuela_result.keywords_matched)
        
        # Check Chevron
        chevron_result = self._matcher.match_chevron(search_text)
        if chevron_result.is_match:
            event.mark_chevron_related(chevron_result.keywords_matched)
    
    async def get_last_poll(self) -> Optional[PollRun]:
        """Get the most recent poll run."""
        polls = await self._polls.find_latest(limit=1)
        return polls[0] if polls else None
    
    async def get_last_successful_poll(self) -> Optional[PollRun]:
        """Get the most recent successful poll run."""
        return await self._polls.find_last_successful()
