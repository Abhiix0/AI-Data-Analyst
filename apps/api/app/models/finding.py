"""Finding database model."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin, JSON_TYPE

if TYPE_CHECKING:
    from apps.api.app.models.analysis_run import AnalysisRun


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

    # Relationships
    run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun",
        back_populates="findings",
    )
