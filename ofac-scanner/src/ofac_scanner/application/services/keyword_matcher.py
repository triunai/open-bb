"""
Keyword Matcher Service

Provides keyword matching logic for detecting Venezuela and Chevron
related events. Extracted into its own service for testability
and single responsibility.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchResult:
    """Result of keyword matching."""
    
    is_match: bool
    keywords_matched: list[str]


class KeywordMatcher:
    """
    Matches event text against configured keyword lists.
    
    This service encapsulates the keyword matching logic, making it
    easy to test and modify without touching other services.
    """
    
    # Venezuela-related keywords (case-insensitive)
    VENEZUELA_KEYWORDS: frozenset[str] = frozenset([
        "venezuela",
        "venezuelan",
        "maduro",
        "pdvsa",
        "citgo",
        "petroleo",
        "bolivarian",
        "caracas",
    ])
    
    # Chevron-related keywords (case-insensitive)
    CHEVRON_KEYWORDS: frozenset[str] = frozenset([
        "chevron",
        "cvx",
        "oil license",
        "petroleum authorization",
        "oil production license",
        "energy license",
    ])
    
    # General License keywords (for high-priority events)
    GENERAL_LICENSE_KEYWORDS: frozenset[str] = frozenset([
        "general license",
        "gl ",
        "amended general license",
        "issuance of",
    ])
    
    def match_venezuela(self, text: str) -> MatchResult:
        """
        Check if text contains Venezuela-related keywords.
        
        Args:
            text: Text to search (title, category, etc.)
            
        Returns:
            MatchResult with match status and matched keywords
        """
        return self._match_keywords(text, self.VENEZUELA_KEYWORDS)
    
    def match_chevron(self, text: str) -> MatchResult:
        """
        Check if text contains Chevron-related keywords.
        
        Args:
            text: Text to search
            
        Returns:
            MatchResult with match status and matched keywords
        """
        return self._match_keywords(text, self.CHEVRON_KEYWORDS)
    
    def match_general_license(self, text: str) -> MatchResult:
        """
        Check if text indicates a General License.
        
        Args:
            text: Text to search
            
        Returns:
            MatchResult with match status and matched keywords
        """
        return self._match_keywords(text, self.GENERAL_LICENSE_KEYWORDS)
    
    def _match_keywords(
        self,
        text: str,
        keywords: frozenset[str],
    ) -> MatchResult:
        """
        Match text against a set of keywords.
        
        Args:
            text: Text to search
            keywords: Set of keywords to match
            
        Returns:
            MatchResult with all matched keywords
        """
        text_lower = text.lower()
        matched = [kw for kw in keywords if kw in text_lower]
        return MatchResult(
            is_match=len(matched) > 0,
            keywords_matched=matched,
        )
    
    def compute_search_text(
        self,
        title: str,
        category: str | None = None,
    ) -> str:
        """
        Combine event fields into searchable text.
        
        Args:
            title: Event title
            category: Event category (optional)
            
        Returns:
            Combined lowercase text for searching
        """
        parts = [title]
        if category:
            parts.append(category)
        return " ".join(parts).lower()
