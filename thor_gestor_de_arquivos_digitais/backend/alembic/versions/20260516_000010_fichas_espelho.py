"""add ficha espelho templates

Revision ID: 20260516_000010
Revises: 20260515_000009
Create Date: 2026-05-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260516_000010"
down_revision = "20260515_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "modelos_ficha_espelho",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("campos", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tamanho_papel", sa.String(length=20), nullable=False),
        sa.Column("orientacao", sa.String(length=20), nullable=False),
        sa.Column("colunas", sa.Integer(), nullable=False),
        sa.Column("largura_cm", sa.Float(), nullable=False, server_default="18.6"),
        sa.Column("altura_cm", sa.Float(), nullable=False, server_default="27.3"),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index("ix_modelos_ficha_espelho_nome", "modelos_ficha_espelho", ["nome"])
    op.create_index("ix_modelos_ficha_espelho_ativo", "modelos_ficha_espelho", ["ativo"])
    op.execute(
        """
        INSERT INTO modelos_ficha_espelho
            (nome, descricao, campos, tamanho_papel, orientacao, colunas, largura_cm, altura_cm, ativo)
        VALUES
            (
                'Ficha espelho padrão',
                'Modelo padrão com os metadados essenciais da caixa.',
                '["logo_instituicao", "unidade_produtora", "fundo", "classe", "subclasse", "descricao_conteudo", "data_limite", "identificador_caixa", "codigo_barras"]'::jsonb,
                'A4',
                'RETRATO',
                1,
                18.6,
                27.3,
                true
            )
        ON CONFLICT (nome) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_modelos_ficha_espelho_ativo", table_name="modelos_ficha_espelho")
    op.drop_index("ix_modelos_ficha_espelho_nome", table_name="modelos_ficha_espelho")
    op.drop_table("modelos_ficha_espelho")
