"""Dataset database model."""
from __future__ import annotations
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.app.models.user import User
    from apps.api.app.models.dataset_version import DatasetVersion


class Dataset(Base, TimestampMixin):
    """Top-level dataset entity owned by a user."""
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="datasets",
    )
    versions: Mapped[List[DatasetVersion]] = relationship(
        "DatasetVersion",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="desc(DatasetVersion.created_at)",
    )
