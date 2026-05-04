"""create research instruments

Revision ID: 20260504_000007
Revises: 20260428_000006
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op

revision = "20260504_000007"
down_revision = "20260428_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS instrumentos_pesquisa (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(255) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            descricao TEXT,
            status VARCHAR(30) NOT NULL DEFAULT 'RASCUNHO',
            visibilidade VARCHAR(30) NOT NULL DEFAULT 'INTERNO',
            responsavel VARCHAR(255),
            criado_em TIMESTAMP NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS ix_instrumentos_pesquisa_nome
            ON instrumentos_pesquisa(nome);

        CREATE INDEX IF NOT EXISTS ix_instrumentos_pesquisa_tipo
            ON instrumentos_pesquisa(tipo);

        CREATE INDEX IF NOT EXISTS ix_instrumentos_pesquisa_status
            ON instrumentos_pesquisa(status);

        CREATE INDEX IF NOT EXISTS ix_instrumentos_pesquisa_visibilidade
            ON instrumentos_pesquisa(visibilidade);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_instrumentos_pesquisa_visibilidade;
        DROP INDEX IF EXISTS ix_instrumentos_pesquisa_status;
        DROP INDEX IF EXISTS ix_instrumentos_pesquisa_tipo;
        DROP INDEX IF EXISTS ix_instrumentos_pesquisa_nome;
        DROP TABLE IF EXISTS instrumentos_pesquisa;
        """
    )
