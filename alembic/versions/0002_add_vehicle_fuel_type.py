"""add vehicle fuel type

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-08 17:48:43.321505

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("vehicles", sa.Column("fuel_type", sa.String(length=20), server_default="diesel", nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("vehicles", "fuel_type")
