"""
OFAC Web Scraper

Concrete implementation of the OFACScraper interface.
Handles HTTP requests and HTML parsing of OFAC pages.
"""

import asyncio
import random
import re
from datetime import datetime, date
from typing import Optional

import httpx
import structlog
from bs4 import BeautifulSoup

from ofac_scanner.config import get_settings
from ofac_scanner.application.interfaces.scraper import (
    OFACScraper,
    ScrapedEvent,
    ScrapeResult,
)


logger = structlog.get_logger(__name__)


class HTTPOFACScraper(OFACScraper):
    """
    HTTP-based implementation of OFAC page scraping.
    
    Uses httpx for async HTTP requests and BeautifulSoup
    for HTML parsing. Implements retry logic with exponential
    backoff.
    """
    
    # Known category strings to filter out (navigation links)
    SKIP_TITLES = frozenset([
        "Sanctions List Updates",
        "Regulations and Guidance",
        "Enforcement Actions",
        "Next",
        "Previous",
    ])
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize the scraper.
        
        Args:
            base_url: OFAC website base URL (default from settings)
            timeout: Request timeout in seconds (default from settings)
            max_retries: Maximum retry attempts (default from settings)
        """
        settings = get_settings()
        self._base_url = base_url or settings.ofac_base_url
        self._timeout = timeout or settings.request_timeout_seconds
        self._max_retries = max_retries or settings.poll_max_retries
    
    async def scrape_recent_actions(self) -> ScrapeResult:
        """
        Scrape the OFAC Recent Actions page.
        
        Returns:
            ScrapeResult with extracted events and raw HTML
        """
        url = f"{self._base_url}/recent-actions"
        return await self.scrape_url(url)
    
    async def scrape_url(self, url: str) -> ScrapeResult:
        """
        Scrape a specific OFAC page.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapeResult with extracted events and raw HTML
        """
        log = logger.bind(url=url)
        log.info("Starting page scrape")
        
        try:
            html = await self._fetch_with_retry(url)
            events = self._parse_recent_actions(html, url)
            
            log.info(
                "Scrape successful",
                events_extracted=len(events),
            )
            
            return ScrapeResult(
                url=url,
                events=events,
                raw_html=html,
                success=True,
            )
            
        except Exception as e:
            log.error("Scrape failed", error=str(e))
            return ScrapeResult(
                url=url,
                events=[],
                raw_html="",
                success=False,
                error=str(e),
            )
    
    async def _fetch_with_retry(self, url: str) -> str:
        """
        Fetch URL with exponential backoff retry.
        
        Uses sync httpx in a thread pool to avoid Windows asyncio issues
        with async httpx.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string
            
        Raises:
            Exception: If all retries fail
        """
        import concurrent.futures
        
        last_error: Optional[Exception] = None
        
        def sync_fetch() -> str:
            """Sync fetch that runs in thread pool."""
            response = httpx.get(
                url,
                timeout=self._timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
            )
            response.raise_for_status()
            return response.text
        
        for attempt in range(self._max_retries):
            try:
                # Run sync httpx in thread pool to avoid Windows asyncio issues
                loop = asyncio.get_event_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    html = await loop.run_in_executor(pool, sync_fetch)
                    return html
                    
            except Exception as e:
                last_error = e
                
                if attempt < self._max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "Retry after failure",
                        attempt=attempt + 1,
                        delay_seconds=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
        
        raise last_error or Exception("All retries failed")
    
    def _parse_recent_actions(self, html: str, base_url: str) -> list[ScrapedEvent]:
        """
        Parse OFAC Recent Actions page HTML.
        
        The page structure (as of 2026):
        - Links with href="/recent-actions/YYYYMMDD" or "/recent-actions/YYYYMMDD_NN"
        - Link text is the event title
        
        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of extracted events
        """
        soup = BeautifulSoup(html, "lxml")
        events: list[ScrapedEvent] = []
        
        # Find all links to recent actions
        for link in soup.select('a[href*="/recent-actions/"]'):
            href = link.get("href", "")
            title = link.get_text(strip=True)
            
            # Skip empty or navigation links
            if not title or title in self.SKIP_TITLES:
                continue
            
            # Skip if it's just a category filter link
            if "?" in href and "page" not in href:
                continue
            
            # Build full URL
            if href.startswith("/"):
                full_url = f"{self._base_url}{href}"
            else:
                full_url = href
            
            # Extract date from URL pattern
            published_date = self._extract_date_from_url(href)
            
            # Detect category from title
            category = self._detect_category(title)
            
            events.append(ScrapedEvent(
                title=title,
                url=full_url,
                published_date=published_date,
                category=category,
            ))
        
        return events
    
    def _extract_date_from_url(self, href: str) -> Optional[date]:
        """
        Extract publication date from OFAC URL.
        
        URL patterns:
        - /recent-actions/20251219
        - /recent-actions/20251219_33
        
        Args:
            href: URL or path
            
        Returns:
            Parsed date or None
        """
        # Match YYYYMMDD pattern
        match = re.search(r"/recent-actions/(\d{8})", href)
        if match:
            try:
                return datetime.strptime(match.group(1), "%Y%m%d").date()
            except ValueError:
                pass
        return None
    
    def _detect_category(self, title: str) -> Optional[str]:
        """
        Detect event category from title.
        
        Categories are detected by keyword matching.
        
        Args:
            title: Event title
            
        Returns:
            Detected category or None
        """
        title_lower = title.lower()
        
        if "general license" in title_lower:
            return "General Licenses"
        elif "designation" in title_lower:
            return "Designations"
        elif "removal" in title_lower:
            return "Removals"
        elif "settlement" in title_lower:
            return "Enforcement Actions"
        elif "faq" in title_lower or "frequently asked" in title_lower:
            return "FAQs"
        elif "guidance" in title_lower or "advisory" in title_lower:
            return "Guidance"
        
        return None
