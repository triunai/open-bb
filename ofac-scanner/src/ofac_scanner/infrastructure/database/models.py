"""
SQLAlchemy ORM Models

Defines the database schema using SQLAlchemy 2.0 declarative style.
These models map directly to database tables.
"""

from datetime import date, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    
    pass


class PollRunModel(Base):
    """
    Database model for poll runs.
    
    Tracks each execution of the polling job for audit
    and debugging purposes.
    """
    
    __tablename__ = "poll_runs"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
    )
    events_found: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    new_events: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    events: Mapped[list["OFACEventModel"]] = relationship(
        back_populates="poll_run",
        lazy="selectin",
    )
    snapshots: Mapped[list["SnapshotModel"]] = relationship(
        back_populates="poll_run",
        lazy="selectin",
    )
    
    __table_args__ = (
        Index("ix_poll_runs_started_at", "started_at", postgresql_using="btree"),
        Index("ix_poll_runs_status", "status", postgresql_using="btree"),
    )


class SnapshotModel(Base):
    """
    Database model for raw HTML snapshots.
    
    Stores the raw page content for audit trail purposes.
    """
    
    __tablename__ = "ofac_snapshots"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    poll_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("poll_runs.id"),
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    raw_html: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    
    # Relationships
    poll_run: Mapped["PollRunModel"] = relationship(
        back_populates="snapshots",
    )
    
    __table_args__ = (
        Index("ix_snapshots_content_hash", "content_hash", postgresql_using="btree"),
        Index("ix_snapshots_poll_run", "poll_run_id", postgresql_using="btree"),
    )


class OFACEventModel(Base):
    """
    Database model for OFAC events.
    
    This is the core table storing parsed OFAC Recent Actions.
    """
    
    __tablename__ = "ofac_events"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    poll_run_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("poll_runs.id"),
        nullable=True,
    )
    event_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    published_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    is_venezuela_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    is_chevron_related: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    keywords_matched: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    
    # Relationships
    poll_run: Mapped[Optional["PollRunModel"]] = relationship(
        back_populates="events",
    )
    alerts: Mapped[list["AlertModel"]] = relationship(
        back_populates="event",
        lazy="selectin",
    )
    
    __table_args__ = (
        Index("ix_events_hash", "event_hash", unique=True),
        Index(
            "ix_events_venezuela",
            "is_venezuela_related",
            postgresql_where=("is_venezuela_related = true"),
        ),
        Index("ix_events_first_seen", "first_seen_at", postgresql_using="btree"),
        Index("ix_events_published", "published_date", postgresql_using="btree"),
    )


class AlertModel(Base):
    """
    Database model for alerts.
    
    Tracks alerts triggered by OFAC events.
    """
    
    __tablename__ = "alert_log"
    
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ofac_events.id"),
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    confidence_score: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=True,
    )
    rule_matched: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    
    # Relationships
    event: Mapped["OFACEventModel"] = relationship(
        back_populates="alerts",
    )
    
    __table_args__ = (
        Index("ix_alerts_event", "event_id", postgresql_using="btree"),
        Index("ix_alerts_type", "alert_type", postgresql_using="btree"),
        Index(
            "ix_alerts_unacked",
            "acknowledged",
            postgresql_where=("acknowledged = false"),
        ),
    )
