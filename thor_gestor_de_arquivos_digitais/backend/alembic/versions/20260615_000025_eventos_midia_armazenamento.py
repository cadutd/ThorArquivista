"""eventos de midia de armazenamento

Revision ID: 20260615_000025
Revises: 20260614_000024
Create Date: 2026-06-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_000025"
down_revision = "20260614_000024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tipo_evento = postgresql.ENUM(
        "INGESTAO",
        "VALIDACAO",
        "FIXIDEZ",
        "REPLICACAO",
        "MIGRACAO",
        "ACESSO",
        "MOVIMENTACAO",
        "OUTRO",
        name="tipo_evento_preservacao",
        create_type=False,
    )
    resultado_evento = postgresql.ENUM(
        "SUCESSO",
        "FALHA",
        "ALERTA",
        "INDETERMINADO",
        name="resultado_evento_preservacao",
        create_type=False,
    )

    op.create_table(
        "eventos_midia_armazenamento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("id_midia_armazenamento", sa.Integer(), nullable=False),
        sa.Column("tipo_evento", tipo_evento, nullable=False),
        sa.Column(
            "resultado",
            resultado_evento,
            server_default="SUCESSO",
            nullable=False,
        ),
        sa.Column("detalhe", sa.Text(), nullable=True),
        sa.Column("agente", sa.String(length=255), nullable=True),
        sa.Column("correlacao", sa.String(length=255), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_midia_armazenamento"],
            ["midias_armazenamento.id"],
            name="fk_eventos_midia_armazenamento_midia",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_id_midia_armazenamento",
        "eventos_midia_armazenamento",
        ["id_midia_armazenamento"],
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_tipo_evento",
        "eventos_midia_armazenamento",
        ["tipo_evento"],
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_resultado",
        "eventos_midia_armazenamento",
        ["resultado"],
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_correlacao",
        "eventos_midia_armazenamento",
        ["correlacao"],
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_criado_em",
        "eventos_midia_armazenamento",
        ["criado_em"],
    )


def downgrade() -> None:
    op.drop_index("ix_eventos_midia_armazenamento_criado_em", table_name="eventos_midia_armazenamento")
    op.drop_index("ix_eventos_midia_armazenamento_correlacao", table_name="eventos_midia_armazenamento")
    op.drop_index("ix_eventos_midia_armazenamento_resultado", table_name="eventos_midia_armazenamento")
    op.drop_index("ix_eventos_midia_armazenamento_tipo_evento", table_name="eventos_midia_armazenamento")
    op.drop_index(
        "ix_eventos_midia_armazenamento_id_midia_armazenamento",
        table_name="eventos_midia_armazenamento",
    )
    op.drop_table("eventos_midia_armazenamento")
