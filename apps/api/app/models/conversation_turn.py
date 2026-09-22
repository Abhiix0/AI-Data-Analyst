"""Conversation Turn database model for chat history and context retention."""
from __future__ import annotations
import uuid
from typing import Any, Dict, List, TYPE_CHECKING
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.models.base import Base, TimestampMixin, JSON_TYPE

if TYPE_CHECKING:
    from apps.api.app.models.analysis_run import AnalysisRun


class ConversationTurn(Base, TimestampMixin):
    """An individual conversational message pair (user question -> verified agent response)."""
    __tablename__ = "conversation_turns"

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
    turn_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    user_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    assistant_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    findings_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )
    evidence_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON_TYPE,
        nullable=False,
        default=list,
    )

    # Relationships
    run: Mapped[AnalysisRun] = relationship(
        "AnalysisRun",
        back_populates="conversation_turns",
    )
