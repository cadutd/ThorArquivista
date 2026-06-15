"""migracao de midias

Revision ID: 20260615_000028
Revises: 20260615_000027
Create Date: 2026-06-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_000028"
down_revision = "20260615_000027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_midia = postgresql.ENUM(
        "ATIVA",
        "EM_VERIFICACAO",
        "COM_ALERTA",
        "FALHA_INTEGRIDADE",
        "EXPIRADA",
        "EM_MIGRACAO",
        "MIGRADA",
        "DESATIVADA",
        "PERDIDA",
        name="status_midia_armazenamento",
        create_type=False,
    )
    status_migracao = postgresql.ENUM(
        "PLANEJADA",
        "EM_EXECUCAO",
        "AGUARDANDO_VALIDACAO",
        "CONCLUIDA",
        "CANCELADA",
        name="status_migracao_midia",
        create_type=False,
    )
    status_midia.create(op.get_bind(), checkfirst=True)
    status_migracao.create(op.get_bind(), checkfirst=True)

    op.add_column("midias_armazenamento", sa.Column("status", status_midia, server_default="ATIVA", nullable=True))
    op.add_column("midias_armazenamento", sa.Column("midia_origem_id", sa.Integer(), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("data_desativacao", sa.DateTime(timezone=True), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("motivo_desativacao", sa.Text(), nullable=True))
    op.execute("UPDATE midias_armazenamento SET status = CASE WHEN ativo THEN 'ATIVA' ELSE 'DESATIVADA' END::status_midia_armazenamento WHERE status IS NULL")
    op.alter_column("midias_armazenamento", "status", nullable=False)
    op.create_foreign_key("fk_midias_armazenamento_midia_origem", "midias_armazenamento", "midias_armazenamento", ["midia_origem_id"], ["id"])
    op.create_index("ix_midias_armazenamento_status", "midias_armazenamento", ["status"])
    op.create_index("ix_midias_armazenamento_midia_origem_id", "midias_armazenamento", ["midia_origem_id"])

    op.create_table(
        "migracoes_midias",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("midia_origem_id", sa.Integer(), nullable=False),
        sa.Column("midia_destino_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_conclusao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usuario_responsavel_id", sa.String(length=255), nullable=True),
        sa.Column("status", status_migracao, server_default="EM_EXECUCAO", nullable=False),
        sa.Column("motivo_migracao", sa.Text(), nullable=False),
        sa.Column("procedimento_utilizado", sa.Text(), nullable=False),
        sa.Column("software_utilizado", sa.Text(), nullable=True),
        sa.Column("versao_software", sa.Text(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("relatorio_integridade_origem", sa.Text(), nullable=True),
        sa.Column("relatorio_integridade_destino", sa.Text(), nullable=True),
        sa.Column("evento_id", sa.Integer(), nullable=True),
        sa.Column("etapas", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("relatorios", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["evento_id"], ["eventos_midia_armazenamento.id"], name="fk_migracoes_midias_evento"),
        sa.ForeignKeyConstraint(["midia_destino_id"], ["midias_armazenamento.id"], name="fk_migracoes_midias_destino"),
        sa.ForeignKeyConstraint(["midia_origem_id"], ["midias_armazenamento.id"], name="fk_migracoes_midias_origem"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_migracoes_midias_midia_origem_id", "migracoes_midias", ["midia_origem_id"])
    op.create_index("ix_migracoes_midias_midia_destino_id", "migracoes_midias", ["midia_destino_id"])
    op.create_index("ix_migracoes_midias_status", "migracoes_midias", ["status"])
    op.create_index("ix_migracoes_midias_data_inicio", "migracoes_midias", ["data_inicio"])
    op.create_index("ix_migracoes_midias_usuario_responsavel_id", "migracoes_midias", ["usuario_responsavel_id"])


def downgrade() -> None:
    op.drop_index("ix_migracoes_midias_usuario_responsavel_id", table_name="migracoes_midias")
    op.drop_index("ix_migracoes_midias_data_inicio", table_name="migracoes_midias")
    op.drop_index("ix_migracoes_midias_status", table_name="migracoes_midias")
    op.drop_index("ix_migracoes_midias_midia_destino_id", table_name="migracoes_midias")
    op.drop_index("ix_migracoes_midias_midia_origem_id", table_name="migracoes_midias")
    op.drop_table("migracoes_midias")
    op.drop_index("ix_midias_armazenamento_midia_origem_id", table_name="midias_armazenamento")
    op.drop_index("ix_midias_armazenamento_status", table_name="midias_armazenamento")
    op.drop_constraint("fk_midias_armazenamento_midia_origem", "midias_armazenamento", type_="foreignkey")
    op.drop_column("midias_armazenamento", "motivo_desativacao")
    op.drop_column("midias_armazenamento", "data_desativacao")
    op.drop_column("midias_armazenamento", "midia_origem_id")
    op.drop_column("midias_armazenamento", "status")
    postgresql.ENUM(name="status_migracao_midia").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="status_midia_armazenamento").drop(op.get_bind(), checkfirst=True)
