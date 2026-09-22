"""Finding database model."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin, JSON_TYPE

if TYPE_CHECKING:
    from apps.api.app.models.analysis_run import AnalysisRun
    from apps.api.app.models.investigation import Investigation


class Finding(Base, TimestampMixin):
    """Structured analytical insight supported by verified evidence objects."""
    __tablename__ = "findings"

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
    claim: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    evidence_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
        comment="List of Evidence objects with metrics, tools, values, and column refs",
    )
    evidence_strength: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="strong | moderate | weak | insufficient",
    )
    source_columns: Mapped[List[str]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )
    query: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="SQL query or tool call expression used to derive this finding",
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether the user pinned/bookmarked this finding",
    )
    user_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User notes, reflections, or hypotheses attached to this finding",
    )
    parent_finding_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID of the parent finding if this finding emerged from a drill-down investigation",
    )

    # Relationships
    run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun",
        back_populates="findings",
    )
    investigations: Mapped[List[Investigation]] = relationship(
        "Investigation",
        back_populates="parent_finding",
        foreign_keys="[Investigation.parent_finding_id]",
    )
