"""Add conversation_turns table and profile_json column.

Revision ID: 0002_add_conversation_turns
Revises: 0001_initial_schema
Create Date: 2026-09-22 20:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_add_conversation_turns"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add profile_json to analysis_runs if not exists
    op.add_column("analysis_runs", sa.Column("profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # 2. Create conversation_turns table
    op.create_table(
        "conversation_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False, default=0),
        sa.Column("user_message", sa.Text(), nullable=False),
        sa.Column("assistant_message", sa.Text(), nullable=False),
        sa.Column("findings_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_conversation_turns_run_id"), "conversation_turns", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_conversation_turns_run_id"), table_name="conversation_turns")
    op.drop_table("conversation_turns")
    op.drop_column("analysis_runs", "profile_json")
