"""Add briefing_json to dataset_versions.

Revision ID: 0004_add_briefing_json
Revises: 0003_add_saved_findings_and_investigations
Create Date: 2026-09-23 06:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_add_briefing_json"
down_revision: Union[str, None] = "0003_add_saved_findings_and_investigations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dataset_versions", sa.Column("briefing_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("dataset_versions", "briefing_json")
