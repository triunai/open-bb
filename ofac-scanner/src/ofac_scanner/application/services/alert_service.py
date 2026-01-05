"""
Alert Service

Handles alert creation and evaluation for OFAC events.
Determines when alerts should be triggered and with what confidence.
"""

import structlog

from ofac_scanner.domain.entities import OFACEvent, Alert, AlertType
from ofac_scanner.domain.value_objects import ConfidenceScore
from ofac_scanner.application.interfaces import AlertRepository
from ofac_scanner.application.services.keyword_matcher import KeywordMatcher


logger = structlog.get_logger(__name__)


class AlertService:
    """
    Service for evaluating and creating alerts.
    
    This service implements the alert rules from the spec:
    - policy_pistol: Chevron-related
    - venezuela_gl: Venezuela + General License
    - venezuela_new: Any Venezuela event
    """
    
    def __init__(
        self,
        alert_repository: AlertRepository,
        keyword_matcher: KeywordMatcher | None = None,
    ):
        """
        Initialize the alert service.
        
        Args:
            alert_repository: Alert persistence
            keyword_matcher: Keyword matching service
        """
        self._alerts = alert_repository
        self._matcher = keyword_matcher or KeywordMatcher()
    
    async def evaluate_and_alert(self, event: OFACEvent) -> list[Alert]:
        """
        Evaluate an event and create appropriate alerts.
        
        This is the main entry point for alert evaluation.
        Multiple alerts can be created for a single event.
        
        Args:
            event: Event to evaluate
            
        Returns:
            List of created alerts (may be empty)
        """
        alerts: list[Alert] = []
        
        # Check for POLICY PISTOL (highest priority)
        if event.is_policy_pistol:
            alert = await self._create_alert(
                event=event,
                alert_type=AlertType.POLICY_PISTOL,
                confidence=self._compute_confidence(event),
                rule="Venezuela + Chevron keywords matched",
            )
            alerts.append(alert)
            
            logger.critical(
                "🔴 POLICY PISTOL ALERT",
                event_title=event.title,
                keywords=event.keywords_matched,
            )
        
        # Check for Venezuela General License
        elif event.is_venezuela_related:
            search_text = self._matcher.compute_search_text(
                event.title,
                event.category,
            )
            gl_match = self._matcher.match_general_license(search_text)
            
            if gl_match.is_match:
                alert = await self._create_alert(
                    event=event,
                    alert_type=AlertType.VENEZUELA_GL,
                    confidence=self._compute_confidence(event),
                    rule=f"Venezuela + General License: {gl_match.keywords_matched}",
                )
                alerts.append(alert)
                
                logger.warning(
                    "⚠️ Venezuela General License detected",
                    event_title=event.title,
                )
            else:
                # Standard Venezuela event
                alert = await self._create_alert(
                    event=event,
                    alert_type=AlertType.VENEZUELA_NEW,
                    confidence=self._compute_confidence(event),
                    rule=f"Venezuela keywords: {event.keywords_matched}",
                )
                alerts.append(alert)
                
                logger.info(
                    "Venezuela event detected",
                    event_title=event.title,
                )
        
        return alerts
    
    async def _create_alert(
        self,
        event: OFACEvent,
        alert_type: AlertType,
        confidence: ConfidenceScore,
        rule: str,
    ) -> Alert:
        """
        Create and persist an alert.
        
        Args:
            event: Triggering event
            alert_type: Type of alert
            confidence: Confidence score
            rule: Description of what triggered this
            
        Returns:
            The created alert
        """
        alert = Alert.create(
            event_id=event.id,
            alert_type=alert_type,
            confidence=float(confidence),
            rule_matched=rule,
        )
        return await self._alerts.save(alert)
    
    def _compute_confidence(self, event: OFACEvent) -> ConfidenceScore:
        """
        Compute confidence score for an event.
        
        Scoring rules:
        - +0.3 for Venezuela mention
        - +0.3 for General License in title
        - +0.3 for Chevron mention
        - +0.1 for recent date (within 7 days)
        
        Args:
            event: Event to score
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        score = 0.0
        
        # Base: Venezuela mention
        if event.is_venezuela_related:
            score += 0.3
        
        # Boost: General License in title
        search_text = self._matcher.compute_search_text(
            event.title,
            event.category,
        )
        if self._matcher.match_general_license(search_text).is_match:
            score += 0.3
        
        # Boost: Chevron mention
        if event.is_chevron_related:
            score += 0.3
        
        # Boost: Recent date
        if event.published_date:
            from datetime import date
            days_old = (date.today() - event.published_date).days
            if days_old <= 7:
                score += 0.1
        
        return ConfidenceScore(min(score, 1.0))
    
    async def acknowledge_alert(
        self,
        alert: Alert,
        notes: str | None = None,
    ) -> Alert:
        """
        Acknowledge an alert.
        
        Args:
            alert: Alert to acknowledge
            notes: Optional notes about the acknowledgment
            
        Returns:
            Updated alert
        """
        alert.acknowledge(notes)
        return await self._alerts.update(alert)
    
    async def get_unacknowledged(
        self,
        alert_type: AlertType | None = None,
        limit: int = 50,
    ) -> list[Alert]:
        """
        Get unacknowledged alerts.
        
        Args:
            alert_type: Filter by type
            limit: Maximum results
            
        Returns:
            List of unacknowledged alerts
        """
        return await self._alerts.find_unacknowledged(
            alert_type=alert_type,
            limit=limit,
        )
    
    async def count_pending(self) -> int:
        """Get count of unacknowledged alerts."""
        return await self._alerts.count_unacknowledged()
