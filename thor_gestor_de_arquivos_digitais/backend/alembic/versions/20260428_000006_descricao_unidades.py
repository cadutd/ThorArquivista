"""associate archival descriptions with storage units

Revision ID: 20260428_000006
Revises: 20260427_000005
Create Date: 2026-04-28
"""

from __future__ import annotations

from alembic import op

revision = "20260428_000006"
down_revision = "20260427_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS registro_descritivo_unidade_acondicionamento (
            id_registro_descritivo UUID NOT NULL
                REFERENCES registros_descritivos(id)
                ON DELETE CASCADE,
            id_unidade_acondicionamento INTEGER NOT NULL
                REFERENCES unidades_acondicionamento(id)
                ON DELETE CASCADE,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (id_registro_descritivo, id_unidade_acondicionamento)
        );

        CREATE INDEX IF NOT EXISTS ix_registro_descritivo_unidade_registro
            ON registro_descritivo_unidade_acondicionamento(id_registro_descritivo);

        CREATE INDEX IF NOT EXISTS ix_registro_descritivo_unidade_unidade
            ON registro_descritivo_unidade_acondicionamento(id_unidade_acondicionamento);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_registro_descritivo_unidade_unidade;
        DROP INDEX IF EXISTS ix_registro_descritivo_unidade_registro;
        DROP TABLE IF EXISTS registro_descritivo_unidade_acondicionamento;
        """
    )
