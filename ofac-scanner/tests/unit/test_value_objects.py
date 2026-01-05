"""Unit tests for domain value objects."""

from datetime import date

import pytest

from ofac_scanner.domain.value_objects import EventHash, ConfidenceScore


class TestEventHash:
    """Tests for EventHash value object."""
    
    def test_compute_hash(self) -> None:
        """Should compute a stable hash."""
        hash1 = EventHash.compute("Test Title", "https://example.com", date(2025, 1, 1))
        hash2 = EventHash.compute("Test Title", "https://example.com", date(2025, 1, 1))
        
        assert hash1 == hash2
        assert len(hash1.value) == 64
    
    def test_compute_hash_different_inputs(self) -> None:
        """Should produce different hashes for different inputs."""
        hash1 = EventHash.compute("Title A", "https://example.com", date(2025, 1, 1))
        hash2 = EventHash.compute("Title B", "https://example.com", date(2025, 1, 1))
        
        assert hash1 != hash2
    
    def test_compute_hash_normalizes_case(self) -> None:
        """Should normalize case for consistent hashing."""
        hash1 = EventHash.compute("Test Title", "https://example.com", None)
        hash2 = EventHash.compute("TEST TITLE", "HTTPS://EXAMPLE.COM", None)
        
        assert hash1 == hash2
    
    def test_compute_hash_no_date(self) -> None:
        """Should handle missing date."""
        hash1 = EventHash.compute("Test", "https://example.com", None)
        assert len(hash1.value) == 64
    
    def test_short_property(self) -> None:
        """Should return first 8 characters."""
        h = EventHash.compute("Test", "https://example.com", None)
        assert len(h.short) == 8
        assert h.short == h.value[:8]
    
    def test_invalid_hash_value(self) -> None:
        """Should reject invalid hash values."""
        with pytest.raises(ValueError):
            EventHash("")
        
        with pytest.raises(ValueError):
            EventHash("tooshort")
        
        with pytest.raises(ValueError):
            EventHash("g" * 64)  # Invalid hex character


class TestConfidenceScore:
    """Tests for ConfidenceScore value object."""
    
    def test_create_valid_score(self) -> None:
        """Should create valid confidence scores."""
        score = ConfidenceScore(0.75)
        assert score.value == 0.75
    
    def test_boundary_values(self) -> None:
        """Should accept boundary values."""
        assert ConfidenceScore(0.0).value == 0.0
        assert ConfidenceScore(1.0).value == 1.0
    
    def test_invalid_score_below_zero(self) -> None:
        """Should reject negative values."""
        with pytest.raises(ValueError):
            ConfidenceScore(-0.1)
    
    def test_invalid_score_above_one(self) -> None:
        """Should reject values above 1."""
        with pytest.raises(ValueError):
            ConfidenceScore(1.1)
    
    def test_factory_methods(self) -> None:
        """Should create scores via factory methods."""
        assert ConfidenceScore.high().value == 0.9
        assert ConfidenceScore.medium().value == 0.6
        assert ConfidenceScore.low().value == 0.3
        assert ConfidenceScore.zero().value == 0.0
    
    def test_label_property(self) -> None:
        """Should return appropriate labels."""
        assert ConfidenceScore(0.95).label == "critical"
        assert ConfidenceScore(0.75).label == "high"
        assert ConfidenceScore(0.5).label == "medium"
        assert ConfidenceScore(0.2).label == "low"
    
    def test_comparison(self) -> None:
        """Should support comparison operators."""
        low = ConfidenceScore(0.3)
        high = ConfidenceScore(0.9)
        
        assert low < high
        assert high > low
        assert low <= ConfidenceScore(0.3)
        assert high >= ConfidenceScore(0.9)
    
    def test_add(self) -> None:
        """Should add values and clamp to [0, 1]."""
        score = ConfidenceScore(0.5)
        
        new_score = score.add(0.3)
        assert new_score.value == 0.8
        
        clamped = score.add(0.7)
        assert clamped.value == 1.0
        
        clamped_low = ConfidenceScore(0.2).add(-0.5)
        assert clamped_low.value == 0.0
    
    def test_immutability(self) -> None:
        """Should be immutable."""
        score = ConfidenceScore(0.5)
        with pytest.raises(AttributeError):
            score.value = 0.9  # type: ignore
