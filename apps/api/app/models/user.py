"""User database model."""
from __future__ import annotations
import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from apps.api.app.models.dataset import Dataset


class User(Base, TimestampMixin):
    """Registered user owning datasets and runs."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Relationships
    datasets: Mapped[List[Dataset]] = relationship(
        "Dataset",
        back_populates="user",
        cascade="all, delete-orphan",
    )
