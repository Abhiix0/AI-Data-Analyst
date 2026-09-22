"""DatasetVersion database model."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.app.models.dataset import Dataset
    from apps.api.app.models.analysis_run import AnalysisRun


class DatasetVersion(Base, TimestampMixin):
    """Immutable version of an ingested dataset backed by Parquet in object storage."""
    __tablename__ = "dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        comment="Object storage key pointing to the Parquet file",
    )
    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    col_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    schema_json: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationships
    dataset: Mapped[Dataset] = relationship(
        "Dataset",
        back_populates="versions",
    )
    runs: Mapped[List[AnalysisRun]] = relationship(
        "AnalysisRun",
        back_populates="dataset_version",
        cascade="all, delete-orphan",
        order_by="desc(AnalysisRun.started_at)",
    )
