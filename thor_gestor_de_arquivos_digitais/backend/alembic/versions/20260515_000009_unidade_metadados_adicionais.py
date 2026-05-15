"""add unidade acondicionamento metadata fields

Revision ID: 20260515_000009
Revises: 20260504_000008
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op

revision = "20260515_000009"
down_revision = "20260504_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        r"""
        ALTER TABLE unidades_acondicionamento
            ADD COLUMN IF NOT EXISTS produtor VARCHAR(255),
            ADD COLUMN IF NOT EXISTS unidade VARCHAR(255),
            ADD COLUMN IF NOT EXISTS data_limite VARCHAR(255),
            ADD COLUMN IF NOT EXISTS codigo_classificacao VARCHAR(255),
            ADD COLUMN IF NOT EXISTS assunto VARCHAR(500),
            ADD COLUMN IF NOT EXISTS codigo_barra VARCHAR(128),
            ADD COLUMN IF NOT EXISTS informacoes_pacote TEXT;

        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_produtor
            ON unidades_acondicionamento (produtor);
        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_codigo_barra
            ON unidades_acondicionamento (codigo_barra);
        """
    )


def downgrade() -> None:
    op.execute(
        r"""
        DROP INDEX IF EXISTS ix_unidades_acondicionamento_codigo_barra;
        DROP INDEX IF EXISTS ix_unidades_acondicionamento_produtor;

        ALTER TABLE unidades_acondicionamento
            DROP COLUMN IF EXISTS informacoes_pacote,
            DROP COLUMN IF EXISTS codigo_barra,
            DROP COLUMN IF EXISTS assunto,
            DROP COLUMN IF EXISTS codigo_classificacao,
            DROP COLUMN IF EXISTS data_limite,
            DROP COLUMN IF EXISTS unidade,
            DROP COLUMN IF EXISTS produtor;
        """
    )
