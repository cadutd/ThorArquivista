"""init

Revision ID: 20261002_000001
Revises:
Create Date: 2026-10-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261002_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("govbr_sub", sa.String(64), nullable=False),
        sa.Column("cpf", sa.String(20), nullable=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("govbr_sub", name="uq_usuarios_govbr_sub"),
    )
    op.create_index("ix_usuarios_cpf", "usuarios", ["cpf"])

    op.create_table(
        "sessoes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("expira_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_sessoes_token_hash"),
    )
    op.create_index("ix_sessoes_usuario_id", "sessoes", ["usuario_id"])

    op.create_table(
        "instrumentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), server_default="RASCUNHO", nullable=False),
        sa.Column("visibilidade", sa.String(40), server_default="INTERNO", nullable=False),
        sa.Column("schema_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("criado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_instrumentos_nome", "instrumentos", ["nome"])
    op.create_index("ix_instrumentos_status", "instrumentos", ["status"])

    op.create_table(
        "instrumento_campos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("chave", sa.String(100), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("ordem", sa.Integer(), server_default="0", nullable=False),
        sa.Column("obrigatorio", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("multiplo", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("opcoes", postgresql.JSONB(), nullable=True),
        sa.Column("validacoes", postgresql.JSONB(), nullable=True),
        sa.Column("aparece_cadastro", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("aparece_listagem", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("aparece_busca", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("instrumento_id", "chave", name="uq_instrumento_campos_chave"),
    )
    op.create_index("ix_instrumento_campos_instrumento", "instrumento_campos", ["instrumento_id"])


def downgrade() -> None:
    op.drop_table("instrumento_campos")
    op.drop_table("instrumentos")
    op.drop_table("sessoes")
    op.drop_table("usuarios")
