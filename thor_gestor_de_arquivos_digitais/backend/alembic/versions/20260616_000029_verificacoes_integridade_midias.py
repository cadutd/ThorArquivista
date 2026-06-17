"""verificacoes de integridade de midias

Revision ID: 20260616_000029
Revises: 20260615_000028
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260616_000029"
down_revision = "20260615_000028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    resultado = postgresql.ENUM(
        "SUCESSO",
        "FALHA",
        "ALERTA",
        "INCONCLUSIVO",
        name="resultado_verificacao_integridade",
        create_type=False,
    )
    resultado.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "verificacoes_integridade_midias",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("midia_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_fim", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usuario_id", sa.String(length=255), nullable=True),
        sa.Column("resultado", resultado, nullable=False),
        sa.Column("software_utilizado", sa.String(length=255), nullable=True),
        sa.Column("versao_software", sa.String(length=100), nullable=True),
        sa.Column("arquivo_relatorio_id", sa.UUID(), nullable=True),
        sa.Column("total_aips_verificados", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_sucesso", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_falha", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_alerta", sa.Integer(), server_default="0", nullable=False),
        sa.Column("relatorio_json", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("evento_id", sa.Integer(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos_midia_armazenamento.id"], name="fk_verificacoes_integridade_midias_evento"),
        sa.ForeignKeyConstraint(["midia_id"], ["midias_armazenamento.id"], name="fk_verificacoes_integridade_midias_midia"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_verificacoes_integridade_midias_midia_id", "verificacoes_integridade_midias", ["midia_id"])
    op.create_index("ix_verificacoes_integridade_midias_data_inicio", "verificacoes_integridade_midias", ["data_inicio"])
    op.create_index("ix_verificacoes_integridade_midias_resultado", "verificacoes_integridade_midias", ["resultado"])
    op.create_index("ix_verificacoes_integridade_midias_usuario_id", "verificacoes_integridade_midias", ["usuario_id"])
    op.create_index("ix_verificacoes_integridade_midias_evento_id", "verificacoes_integridade_midias", ["evento_id"])


def downgrade() -> None:
    op.drop_index("ix_verificacoes_integridade_midias_evento_id", table_name="verificacoes_integridade_midias")
    op.drop_index("ix_verificacoes_integridade_midias_usuario_id", table_name="verificacoes_integridade_midias")
    op.drop_index("ix_verificacoes_integridade_midias_resultado", table_name="verificacoes_integridade_midias")
    op.drop_index("ix_verificacoes_integridade_midias_data_inicio", table_name="verificacoes_integridade_midias")
    op.drop_index("ix_verificacoes_integridade_midias_midia_id", table_name="verificacoes_integridade_midias")
    op.drop_table("verificacoes_integridade_midias")
    postgresql.ENUM(name="resultado_verificacao_integridade").drop(op.get_bind(), checkfirst=True)
