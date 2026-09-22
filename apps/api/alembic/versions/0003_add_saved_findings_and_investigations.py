"""Add saved findings columns and investigations table.

Revision ID: 0003_add_saved_findings_and_investigations
Revises: 0002_add_conversation_turns
Create Date: 2026-09-22 20:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_add_saved_findings_and_investigations"
down_revision: Union[str, None] = "0002_add_conversation_turns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to findings table
    op.add_column("findings", sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("findings", sa.Column("user_notes", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("parent_finding_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_findings_parent_finding_id_findings",
        "findings",
        "findings",
        ["parent_finding_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_findings_is_pinned"), "findings", ["is_pinned"], unique=False)
    op.create_index(op.f("ix_findings_parent_finding_id"), "findings", ["parent_finding_id"], unique=False)

    # 2. Create investigations table
    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_finding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="completed"),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_finding_id"], ["findings.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_investigations_run_id"), "investigations", ["run_id"], unique=False)
    op.create_index(op.f("ix_investigations_parent_finding_id"), "investigations", ["parent_finding_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_investigations_parent_finding_id"), table_name="investigations")
    op.drop_index(op.f("ix_investigations_run_id"), table_name="investigations")
    op.drop_table("investigations")

    op.drop_index(op.f("ix_findings_parent_finding_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_is_pinned"), table_name="findings")
    op.drop_constraint("fk_findings_parent_finding_id_findings", "findings", type_="foreignkey")
    op.drop_column("findings", "parent_finding_id")
    op.drop_column("findings", "user_notes")
    op.drop_column("findings", "is_pinned")
