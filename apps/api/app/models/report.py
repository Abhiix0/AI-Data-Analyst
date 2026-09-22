"""Report database model."""
from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.app.models.analysis_run import AnalysisRun


class Report(Base, TimestampMixin):
    """Generated analysis report document stored in object storage."""
    __tablename__ = "reports"

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
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        comment="Object storage key pointing to the markdown or pdf report file",
    )

    # Relationships
    run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun",
        back_populates="reports",
    )
