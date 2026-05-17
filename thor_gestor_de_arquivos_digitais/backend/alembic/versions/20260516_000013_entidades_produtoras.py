"""create producer entities

Revision ID: 20260516_000013
Revises: 20260516_000012
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op

revision = "20260516_000013"
down_revision = "20260516_000012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS entidades_produtoras (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            nome VARCHAR(255) NOT NULL,
            nome_normalizado VARCHAR(255),
            sigla VARCHAR(50),
            codigo_referencia VARCHAR(100),
            tipo_entidade VARCHAR(50) NOT NULL,
            natureza_juridica VARCHAR(100),
            data_inicio DATE,
            data_fim DATE,
            entidade_ativa BOOLEAN NOT NULL DEFAULT TRUE,
            historico TEXT,
            competencias_funcoes TEXT,
            observacoes TEXT,
            email VARCHAR(255),
            telefone VARCHAR(50),
            site VARCHAR(255),
            endereco_logradouro VARCHAR(255),
            endereco_numero VARCHAR(50),
            endereco_complemento VARCHAR(100),
            endereco_bairro VARCHAR(100),
            endereco_municipio VARCHAR(100),
            endereco_uf VARCHAR(2),
            endereco_cep VARCHAR(20),
            endereco_pais VARCHAR(100) DEFAULT 'Brasil',
            id_entidade_superior UUID NULL,
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT fk_entidade_superior
                FOREIGN KEY (id_entidade_superior)
                REFERENCES entidades_produtoras(id)
                ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_nome
            ON entidades_produtoras(nome);
        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_nome_normalizado
            ON entidades_produtoras(nome_normalizado);
        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_sigla
            ON entidades_produtoras(sigla);
        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_codigo_referencia
            ON entidades_produtoras(codigo_referencia);
        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_tipo_entidade
            ON entidades_produtoras(tipo_entidade);
        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_entidade_ativa
            ON entidades_produtoras(entidade_ativa);
        CREATE INDEX IF NOT EXISTS ix_entidades_produtoras_superior
            ON entidades_produtoras(id_entidade_superior);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_entidades_produtoras_superior;
        DROP INDEX IF EXISTS ix_entidades_produtoras_entidade_ativa;
        DROP INDEX IF EXISTS ix_entidades_produtoras_tipo_entidade;
        DROP INDEX IF EXISTS ix_entidades_produtoras_codigo_referencia;
        DROP INDEX IF EXISTS ix_entidades_produtoras_sigla;
        DROP INDEX IF EXISTS ix_entidades_produtoras_nome_normalizado;
        DROP INDEX IF EXISTS ix_entidades_produtoras_nome;
        DROP TABLE IF EXISTS entidades_produtoras;
        """
    )
