"""evento de reativacao de midia

Revision ID: 20260615_000027
Revises: 20260615_000026
Create Date: 2026-06-15
"""

from __future__ import annotations

from alembic import op


revision = "20260615_000027"
down_revision = "20260615_000026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TYPE tipo_evento_midia_armazenamento
        ADD VALUE IF NOT EXISTS 'REATIVACAO_MIDIA'
        AFTER 'ATUALIZACAO_MIDIA'
        """
    )


def downgrade() -> None:
    # PostgreSQL nao permite remover valores de enum de forma segura sem recriar o tipo.
    pass
