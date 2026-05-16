"""normalize ficha espelho dimensions

Revision ID: 20260516_000012
Revises: 20260516_000011
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op

revision = "20260516_000012"
down_revision = "20260516_000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE modelos_ficha_espelho
            ALTER COLUMN largura_cm SET DEFAULT 18.6,
            ALTER COLUMN altura_cm SET DEFAULT 27.3;

        UPDATE modelos_ficha_espelho
           SET largura_cm = LEAST(
                   largura_cm,
                   CASE
                       WHEN tamanho_papel = 'CARTA' AND orientacao = 'PAISAGEM'
                           THEN (27.94 - 2.4 - (0.2 * GREATEST(colunas - 1, 0))) / colunas
                       WHEN tamanho_papel = 'CARTA'
                           THEN (21.59 - 2.4 - (0.2 * GREATEST(colunas - 1, 0))) / colunas
                       WHEN orientacao = 'PAISAGEM'
                           THEN (29.7 - 2.4 - (0.2 * GREATEST(colunas - 1, 0))) / colunas
                       ELSE (21.0 - 2.4 - (0.2 * GREATEST(colunas - 1, 0))) / colunas
                   END
               ),
               altura_cm = LEAST(
                   altura_cm,
                   CASE
                       WHEN tamanho_papel = 'CARTA' AND orientacao = 'PAISAGEM'
                           THEN 21.59 - 2.4
                       WHEN tamanho_papel = 'CARTA'
                           THEN 27.94 - 2.4
                       WHEN orientacao = 'PAISAGEM'
                           THEN 21.0 - 2.4
                       ELSE 29.7 - 2.4
                   END
               );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE modelos_ficha_espelho
            ALTER COLUMN largura_cm SET DEFAULT 21.0,
            ALTER COLUMN altura_cm SET DEFAULT 29.7;
        """
    )
