"""add ficha espelho dimensions

Revision ID: 20260516_000011
Revises: 20260516_000010
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op

revision = "20260516_000011"
down_revision = "20260516_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE modelos_ficha_espelho
            ADD COLUMN IF NOT EXISTS largura_cm DOUBLE PRECISION NOT NULL DEFAULT 18.6,
            ADD COLUMN IF NOT EXISTS altura_cm DOUBLE PRECISION NOT NULL DEFAULT 27.3;

        UPDATE modelos_ficha_espelho
           SET largura_cm = LEAST(largura_cm, 18.6),
               altura_cm = LEAST(altura_cm, 27.3)
         WHERE tamanho_papel = 'A4'
           AND orientacao = 'RETRATO'
           AND colunas = 1;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE modelos_ficha_espelho
            DROP COLUMN IF EXISTS altura_cm,
            DROP COLUMN IF EXISTS largura_cm;
        """
    )
