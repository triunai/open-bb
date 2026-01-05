"""
OFAC Scraper Interface

Defines the contract for fetching and parsing OFAC web pages.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ScrapedEvent:
    """
    Raw event data extracted from OFAC page.
    
    This is a simple data transfer object used between the
    scraper and the polling service. The polling service
    will convert this to a proper OFACEvent entity.
    """
    
    title: str
    url: str
    published_date: Optional[date] = None
    category: Optional[str] = None


@dataclass
class ScrapeResult:
    """
    Result of a scraping operation.
    
    Contains both the extracted events and the raw HTML
    for audit trail purposes.
    """
    
    url: str
    events: list[ScrapedEvent]
    raw_html: str
    success: bool = True
    error: Optional[str] = None


class OFACScraper(ABC):
    """
    Abstract interface for OFAC page scraping.
    
    Implementations of this interface handle the actual HTTP
    requests and HTML parsing. The application layer doesn't
    need to know about BeautifulSoup, httpx, or HTML structure.
    """
    
    @abstractmethod
    async def scrape_recent_actions(self) -> ScrapeResult:
        """
        Scrape the OFAC Recent Actions page.
        
        Returns:
            ScrapeResult containing extracted events and raw HTML
            
        Raises:
            ScrapingError: If the scraping operation fails
        """
        ...
    
    @abstractmethod
    async def scrape_url(self, url: str) -> ScrapeResult:
        """
        Scrape a specific OFAC page.
        
        Args:
            url: The URL to scrape
            
        Returns:
            ScrapeResult containing extracted events and raw HTML
        """
        ...
