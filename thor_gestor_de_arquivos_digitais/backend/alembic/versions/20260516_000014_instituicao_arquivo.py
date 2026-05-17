"""create archive institution singleton

Revision ID: 20260516_000014
Revises: 20260516_000013
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op

revision = "20260516_000014"
down_revision = "20260516_000013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS instituicao_arquivo (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            singleton_key BOOLEAN NOT NULL DEFAULT TRUE,
            nome VARCHAR(255) NOT NULL,
            sigla VARCHAR(50),
            codigo_referencia VARCHAR(100),
            natureza_juridica VARCHAR(100),
            esfera_administrativa VARCHAR(50),
            cnpj VARCHAR(20),
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
            responsavel_nome VARCHAR(255),
            responsavel_cargo VARCHAR(255),
            responsavel_email VARCHAR(255),
            responsavel_telefone VARCHAR(50),
            historico TEXT,
            missao TEXT,
            observacoes TEXT,
            criada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizada_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_instituicao_arquivo_singleton UNIQUE (singleton_key)
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS instituicao_arquivo;")
