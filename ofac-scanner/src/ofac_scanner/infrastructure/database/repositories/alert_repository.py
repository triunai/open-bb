"""
SQL Alert Repository

Concrete implementation of AlertRepository using SQLAlchemy.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ofac_scanner.domain.entities import Alert, AlertType
from ofac_scanner.domain.value_objects import ConfidenceScore
from ofac_scanner.application.interfaces import AlertRepository
from ofac_scanner.infrastructure.database.models import AlertModel


class SQLAlertRepository(AlertRepository):
    """
    SQLAlchemy implementation of the AlertRepository interface.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self._session = session
    
    async def save(self, alert: Alert) -> Alert:
        """Persist an alert to the database."""
        model = self._to_model(alert)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)
    
    async def find_by_id(self, alert_id: UUID) -> Optional[Alert]:
        """Find an alert by its ID."""
        result = await self._session.execute(
            select(AlertModel).where(AlertModel.id == alert_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def find_by_event(self, event_id: UUID) -> list[Alert]:
        """Find all alerts for a given event."""
        result = await self._session.execute(
            select(AlertModel)
            .where(AlertModel.event_id == event_id)
            .order_by(AlertModel.triggered_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars()]
    
    async def find_unacknowledged(
        self,
        alert_type: Optional[AlertType] = None,
        limit: int = 50,
    ) -> list[Alert]:
        """Find unacknowledged alerts."""
        query = (
            select(AlertModel)
            .where(AlertModel.acknowledged == False)
        )
        
        if alert_type:
            query = query.where(AlertModel.alert_type == alert_type.value)
        
        query = query.order_by(AlertModel.triggered_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars()]
    
    async def find_latest(self, limit: int = 20) -> list[Alert]:
        """Get the most recent alerts."""
        result = await self._session.execute(
            select(AlertModel)
            .order_by(AlertModel.triggered_at.desc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]
    
    async def update(self, alert: Alert) -> Alert:
        """Update an existing alert."""
        result = await self._session.execute(
            select(AlertModel).where(AlertModel.id == alert.id)
        )
        model = result.scalar_one()
        
        # Update fields
        model.acknowledged = alert.acknowledged
        model.acknowledged_at = alert.acknowledged_at
        model.notes = alert.notes
        
        await self._session.flush()
        return self._to_entity(model)
    
    async def count_unacknowledged(self) -> int:
        """Get count of unacknowledged alerts."""
        result = await self._session.execute(
            select(func.count())
            .select_from(AlertModel)
            .where(AlertModel.acknowledged == False)
        )
        return result.scalar_one()
    
    def _to_model(self, entity: Alert) -> AlertModel:
        """Convert domain entity to ORM model."""
        return AlertModel(
            id=entity.id,
            event_id=entity.event_id,
            alert_type=entity.alert_type.value,
            triggered_at=entity.triggered_at,
            confidence_score=float(entity.confidence),
            rule_matched=entity.rule_matched,
            acknowledged=entity.acknowledged,
            acknowledged_at=entity.acknowledged_at,
            notes=entity.notes,
        )
    
    def _to_entity(self, model: AlertModel) -> Alert:
        """Convert ORM model to domain entity."""
        return Alert(
            id=model.id,
            event_id=model.event_id,
            alert_type=AlertType(model.alert_type),
            triggered_at=model.triggered_at,
            confidence=ConfidenceScore(float(model.confidence_score or 0)),
            rule_matched=model.rule_matched,
            acknowledged=model.acknowledged,
            acknowledged_at=model.acknowledged_at,
            notes=model.notes,
        )
