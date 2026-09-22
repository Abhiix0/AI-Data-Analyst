"""Investigation database model."""
from __future__ import annotations
import uuid
from typing import Any, Dict, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin, JSON_TYPE

if TYPE_CHECKING:
    from apps.api.app.models.analysis_run import AnalysisRun
    from apps.api.app.models.finding import Finding


class Investigation(Base, TimestampMixin):
    """A drill-down exploration record tracking deep dive inquiries on findings."""
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_finding_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Investigation prompt or question asked",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="completed",
        nullable=False,
        comment="completed | failed | in_progress",
    )
    findings_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    result_json: Mapped[Dict[str, Any]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=dict,
        comment="Stores validation status, synthesized findings, child finding IDs, evidence refs",
    )

    # Relationships
    run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun",
        back_populates="investigations",
    )
    parent_finding: Mapped[Optional[Finding]] = relationship(
        "Finding",
        back_populates="investigations",
        foreign_keys=[parent_finding_id],
    )
