"""system parameters

Revision ID: 20260426_000003
Revises: 20260425_000002
Create Date: 2026-04-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260426_000003"
down_revision = "000002_storage_locations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        r"""
        CREATE TABLE IF NOT EXISTS parametros_sistema (
            chave VARCHAR(120) PRIMARY KEY,
            valor JSONB NOT NULL,
            descricao TEXT,
            atualizado_em TIMESTAMPTZ DEFAULT now()
        );
        """
    )
    op.execute(
        sa.text(
            r"""
        INSERT INTO parametros_sistema (chave, valor, descricao)
        VALUES (
            'enderecamento',
            CAST(:valor AS JSONB),
            'Parametrizações do módulo de endereçamento.'
        )
        ON CONFLICT (chave) DO NOTHING;
            """
        ).bindparams(
            valor='{"digitos_codigo_estrutura":{"corredor":2,"modulo":2,"estante":2}}',
        )
    )


def downgrade() -> None:
    op.execute(
        r"""
        DELETE FROM parametros_sistema
        WHERE chave = 'enderecamento';

        DROP TABLE IF EXISTS parametros_sistema;
        """
    )
