"""indice ultima checagem de midias

Revision ID: 20260616_000030
Revises: 20260616_000029
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op


revision = "20260616_000030"
down_revision = "20260616_000029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_midias_armazenamento_ultima_checagem_integridade",
        "midias_armazenamento",
        ["ultima_checagem_integridade"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_midias_armazenamento_ultima_checagem_integridade",
        table_name="midias_armazenamento",
    )
