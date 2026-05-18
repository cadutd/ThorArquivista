"""add responsible user to admission process

Revision ID: 20260518_000017
Revises: 20260517_000016
Create Date: 2026-05-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260518_000017"
down_revision = "20260517_000016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "processos_admissao",
        sa.Column("nome_usuario_responsavel", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("processos_admissao", "nome_usuario_responsavel")
