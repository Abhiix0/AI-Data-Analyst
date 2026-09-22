"""AnalysisRun database model."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, utc_now, JSON_TYPE

if TYPE_CHECKING:
    from apps.api.app.models.dataset_version import DatasetVersion
    from apps.api.app.models.finding import Finding
    from apps.api.app.models.report import Report
    from apps.api.app.models.conversation_turn import ConversationTurn


class AnalysisRun(Base):
    """An execution run of the analysis engine or agent over a dataset version."""
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        comment="pending | running | completed | failed",
    )
    profile_json: Mapped[Optional[dict]] = mapped_column(
        JSON_TYPE,
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    dataset_version: Mapped[DatasetVersion] = relationship(
        "DatasetVersion",
        back_populates="runs",
    )
    findings: Mapped[List[Finding]] = relationship(
        "Finding",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    reports: Mapped[List[Report]] = relationship(
        "Report",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    conversation_turns: Mapped[List[ConversationTurn]] = relationship(
        "ConversationTurn",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.turn_index",
    )
