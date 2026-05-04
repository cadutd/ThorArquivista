"""create research instrument fields

Revision ID: 20260504_000008
Revises: 20260504_000007
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op

revision = "20260504_000008"
down_revision = "20260504_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS instrumento_campos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            instrumento_id UUID NOT NULL REFERENCES instrumentos_pesquisa(id) ON DELETE CASCADE,
            nome VARCHAR(255) NOT NULL,
            chave VARCHAR(100) NOT NULL,
            tipo VARCHAR(50) NOT NULL,
            ordem INTEGER NOT NULL DEFAULT 0,
            obrigatorio BOOLEAN NOT NULL DEFAULT false,
            multiplo BOOLEAN NOT NULL DEFAULT false,
            valor_padrao TEXT,
            placeholder TEXT,
            ajuda TEXT,
            aparece_cadastro BOOLEAN NOT NULL DEFAULT true,
            aparece_listagem BOOLEAN NOT NULL DEFAULT true,
            aparece_busca BOOLEAN NOT NULL DEFAULT true,
            filtro_avancado BOOLEAN NOT NULL DEFAULT false,
            facetavel BOOLEAN NOT NULL DEFAULT false,
            ordenavel BOOLEAN NOT NULL DEFAULT false,
            opcoes JSONB,
            validacoes JSONB,
            criado_em TIMESTAMP NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE (instrumento_id, chave)
        );

        CREATE INDEX IF NOT EXISTS ix_instrumento_campos_instrumento_id
            ON instrumento_campos(instrumento_id);

        CREATE INDEX IF NOT EXISTS ix_instrumento_campos_tipo
            ON instrumento_campos(tipo);

        CREATE INDEX IF NOT EXISTS ix_instrumento_campos_ordem
            ON instrumento_campos(instrumento_id, ordem);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_instrumento_campos_ordem;
        DROP INDEX IF EXISTS ix_instrumento_campos_tipo;
        DROP INDEX IF EXISTS ix_instrumento_campos_instrumento_id;
        DROP TABLE IF EXISTS instrumento_campos;
        """
    )
