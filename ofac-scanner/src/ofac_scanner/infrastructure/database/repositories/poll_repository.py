"""
SQL Poll Run Repository

Concrete implementation of PollRunRepository using SQLAlchemy.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ofac_scanner.domain.entities import PollRun, PollStatus
from ofac_scanner.application.interfaces import PollRunRepository
from ofac_scanner.infrastructure.database.models import PollRunModel


class SQLPollRunRepository(PollRunRepository):
    """
    SQLAlchemy implementation of the PollRunRepository interface.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize with a database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self._session = session
    
    async def save(self, poll_run: PollRun) -> PollRun:
        """Persist a poll run to the database."""
        model = self._to_model(poll_run)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)
    
    async def find_by_id(self, poll_run_id: UUID) -> Optional[PollRun]:
        """Find a poll run by its ID."""
        result = await self._session.execute(
            select(PollRunModel).where(PollRunModel.id == poll_run_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def find_latest(self, limit: int = 10) -> list[PollRun]:
        """Get the most recent poll runs."""
        result = await self._session.execute(
            select(PollRunModel)
            .order_by(PollRunModel.started_at.desc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars()]
    
    async def find_last_successful(self) -> Optional[PollRun]:
        """Get the most recent successful poll run."""
        result = await self._session.execute(
            select(PollRunModel)
            .where(PollRunModel.status == PollStatus.SUCCESS.value)
            .order_by(PollRunModel.completed_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def update(self, poll_run: PollRun) -> PollRun:
        """Update an existing poll run."""
        result = await self._session.execute(
            select(PollRunModel).where(PollRunModel.id == poll_run.id)
        )
        model = result.scalar_one()
        
        # Update fields
        model.completed_at = poll_run.completed_at
        model.status = poll_run.status.value
        model.events_found = poll_run.events_found
        model.new_events = poll_run.new_events
        model.error_message = poll_run.error_message
        
        await self._session.flush()
        return self._to_entity(model)
    
    def _to_model(self, entity: PollRun) -> PollRunModel:
        """Convert domain entity to ORM model."""
        return PollRunModel(
            id=entity.id,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            status=entity.status.value,
            events_found=entity.events_found,
            new_events=entity.new_events,
            error_message=entity.error_message,
        )
    
    def _to_entity(self, model: PollRunModel) -> PollRun:
        """Convert ORM model to domain entity."""
        return PollRun(
            id=model.id,
            started_at=model.started_at,
            completed_at=model.completed_at,
            status=PollStatus(model.status),
            events_found=model.events_found,
            new_events=model.new_events,
            error_message=model.error_message,
        )
