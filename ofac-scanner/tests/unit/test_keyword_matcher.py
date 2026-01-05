"""Unit tests for the KeywordMatcher service."""

import pytest

from ofac_scanner.application.services.keyword_matcher import KeywordMatcher


class TestKeywordMatcher:
    """Tests for KeywordMatcher."""
    
    @pytest.fixture
    def matcher(self) -> KeywordMatcher:
        """Create a KeywordMatcher instance."""
        return KeywordMatcher()
    
    # -------------------------------------------------------------------------
    # Venezuela Matching
    # -------------------------------------------------------------------------
    
    def test_match_venezuela_positive(self, matcher: KeywordMatcher) -> None:
        """Should match Venezuela-related text."""
        result = matcher.match_venezuela("Venezuela-related Designations")
        assert result.is_match is True
        assert "venezuela" in result.keywords_matched
    
    def test_match_venezuela_pdvsa(self, matcher: KeywordMatcher) -> None:
        """Should match PDVSA (Venezuelan oil company)."""
        result = matcher.match_venezuela("PDVSA sanctions update")
        assert result.is_match is True
        assert "pdvsa" in result.keywords_matched
    
    def test_match_venezuela_maduro(self, matcher: KeywordMatcher) -> None:
        """Should match Maduro references."""
        result = matcher.match_venezuela("Maduro regime designations")
        assert result.is_match is True
        assert "maduro" in result.keywords_matched
    
    def test_match_venezuela_negative(self, matcher: KeywordMatcher) -> None:
        """Should not match unrelated text."""
        result = matcher.match_venezuela("Russia-related sanctions")
        assert result.is_match is False
        assert len(result.keywords_matched) == 0
    
    def test_match_venezuela_case_insensitive(self, matcher: KeywordMatcher) -> None:
        """Should match regardless of case."""
        result = matcher.match_venezuela("VENEZUELA General License")
        assert result.is_match is True
    
    # -------------------------------------------------------------------------
    # Chevron Matching
    # -------------------------------------------------------------------------
    
    def test_match_chevron_positive(self, matcher: KeywordMatcher) -> None:
        """Should match Chevron references."""
        result = matcher.match_chevron("Chevron oil license extension")
        assert result.is_match is True
        assert "chevron" in result.keywords_matched
    
    def test_match_chevron_cvx(self, matcher: KeywordMatcher) -> None:
        """Should match CVX ticker."""
        result = matcher.match_chevron("CVX authorization update")
        assert result.is_match is True
        assert "cvx" in result.keywords_matched
    
    def test_match_chevron_oil_license(self, matcher: KeywordMatcher) -> None:
        """Should match oil license phrase."""
        result = matcher.match_chevron("New oil license issued")
        assert result.is_match is True
        assert "oil license" in result.keywords_matched
    
    def test_match_chevron_negative(self, matcher: KeywordMatcher) -> None:
        """Should not match unrelated text."""
        result = matcher.match_chevron("ExxonMobil operations")
        assert result.is_match is False
    
    # -------------------------------------------------------------------------
    # General License Matching
    # -------------------------------------------------------------------------
    
    def test_match_general_license(self, matcher: KeywordMatcher) -> None:
        """Should match general license references."""
        result = matcher.match_general_license("Issuance of General License 44")
        assert result.is_match is True
        assert "general license" in result.keywords_matched
    
    def test_match_amended_general_license(self, matcher: KeywordMatcher) -> None:
        """Should match amended general license."""
        result = matcher.match_general_license("Amended General License")
        assert result.is_match is True
    
    # -------------------------------------------------------------------------
    # Combined Text
    # -------------------------------------------------------------------------
    
    def test_compute_search_text(self, matcher: KeywordMatcher) -> None:
        """Should combine title and category."""
        text = matcher.compute_search_text(
            "Venezuela Designations",
            "Sanctions List Updates",
        )
        assert "venezuela designations" in text
        assert "sanctions list updates" in text
    
    def test_compute_search_text_no_category(self, matcher: KeywordMatcher) -> None:
        """Should handle missing category."""
        text = matcher.compute_search_text("Venezuela Designations")
        assert "venezuela designations" in text
