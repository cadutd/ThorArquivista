"""remove meeting document field

Revision ID: 20260518_000018
Revises: 20260518_000017
Create Date: 2026-05-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260518_000018"
down_revision = "20260518_000017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("reunioes_admissao", "ata_documento")


def downgrade() -> None:
    op.add_column(
        "reunioes_admissao",
        sa.Column("ata_documento", sa.String(length=500), nullable=True),
    )
