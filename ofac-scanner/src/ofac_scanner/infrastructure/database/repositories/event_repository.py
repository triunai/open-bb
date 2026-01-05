"""
SQL Event Repository

Concrete implementation of EventRepository using SQLAlchemy.
"""

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ofac_scanner.domain.entities import OFACEvent
from ofac_scanner.domain.value_objects import EventHash
from ofac_scanner.application.interfaces import EventRepository
from ofac_scanner.infrastructure.database.models import OFACEventModel


class SQLEventRepository(EventRepository):
    """
    SQLAlchemy implementation of the EventRepository interface.
    
    This class handles the mapping between domain entities and
    database models, keeping the domain layer clean.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self._session = session
    
    async def save(self, event: OFACEvent) -> OFACEvent:
        """Persist an event to the database."""
        model = self._to_model(event)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)
    
    async def save_many(self, events: Sequence[OFACEvent]) -> list[OFACEvent]:
        """Persist multiple events in a single transaction."""
        models = [self._to_model(e) for e in events]
        self._session.add_all(models)
        await self._session.flush()
        return [self._to_entity(m) for m in models]
    
    async def find_by_id(self, event_id: UUID) -> Optional[OFACEvent]:
        """Find an event by its ID."""
        result = await self._session.execute(
            select(OFACEventModel).where(OFACEventModel.id == event_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def find_by_hash(self, event_hash: EventHash) -> Optional[OFACEvent]:
        """Find an event by its hash."""
        result = await self._session.execute(
            select(OFACEventModel).where(
                OFACEventModel.event_hash == str(event_hash)
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def exists_by_hash(self, event_hash: EventHash) -> bool:
        """Check if an event with the given hash exists."""
        result = await self._session.execute(
            select(func.count()).select_from(OFACEventModel).where(
                OFACEventModel.event_hash == str(event_hash)
            )
        )
        return result.scalar_one() > 0
    
    async def find_latest(self, limit: int = 20) -> list[OFACEvent]:
        """Get the most recent events."""
        result = await self._session.execute(
            select(OFACEventModel)
            .order_by(OFACEventModel.first_seen_at.desc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]
    
    async def find_venezuela_related(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        chevron_only: bool = False,
    ) -> list[OFACEvent]:
        """Get Venezuela-related events."""
        query = (
            select(OFACEventModel)
            .where(OFACEventModel.is_venezuela_related == True)
        )
        
        if since:
            query = query.where(OFACEventModel.first_seen_at >= since)
        
        if chevron_only:
            query = query.where(OFACEventModel.is_chevron_related == True)
        
        query = query.order_by(OFACEventModel.first_seen_at.desc()).limit(limit)
        
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars()]
    
    async def find_since(self, since: datetime) -> list[OFACEvent]:
        """Get events first seen after a given time."""
        result = await self._session.execute(
            select(OFACEventModel)
            .where(OFACEventModel.first_seen_at >= since)
            .order_by(OFACEventModel.first_seen_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars()]
    
    async def count_total(self) -> int:
        """Get total count of all events."""
        result = await self._session.execute(
            select(func.count()).select_from(OFACEventModel)
        )
        return result.scalar_one()
    
    async def count_venezuela(self) -> int:
        """Get count of Venezuela-related events."""
        result = await self._session.execute(
            select(func.count())
            .select_from(OFACEventModel)
            .where(OFACEventModel.is_venezuela_related == True)
        )
        return result.scalar_one()
    
    def _to_model(self, entity: OFACEvent) -> OFACEventModel:
        """Convert domain entity to ORM model."""
        return OFACEventModel(
            id=entity.id,
            poll_run_id=entity.poll_run_id,
            event_hash=str(entity.event_hash),
            title=entity.title,
            url=entity.url,
            published_date=entity.published_date,
            category=entity.category,
            is_venezuela_related=entity.is_venezuela_related,
            is_chevron_related=entity.is_chevron_related,
            keywords_matched=entity.keywords_matched,
            first_seen_at=entity.first_seen_at,
        )
    
    def _to_entity(self, model: OFACEventModel) -> OFACEvent:
        """Convert ORM model to domain entity."""
        return OFACEvent(
            id=model.id,
            poll_run_id=model.poll_run_id,
            event_hash=EventHash(model.event_hash),
            title=model.title,
            url=model.url,
            published_date=model.published_date,
            category=model.category,
            is_venezuela_related=model.is_venezuela_related,
            is_chevron_related=model.is_chevron_related,
            keywords_matched=list(model.keywords_matched),
            first_seen_at=model.first_seen_at,
        )
