"""create eventos de preservacao

Revision ID: 4c25b68d5c40
Revises: a85fd65a16e2
Create Date: 2025-12-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "4c25b68d5c40"
down_revision = "a85fd65a16e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tipo_evento = sa.Enum(
        "ingestao",
        "validacao",
        "fixidez",
        "replicacao",
        "migracao",
        "acesso",
        "movimentacao",
        "outro",
        name="tipo_evento_preservacao",
    )
    resultado_evento = sa.Enum(
        "sucesso",
        "falha",
        "alerta",
        "indeterminado",
        name="resultado_evento_preservacao",
    )

    bind = op.get_bind()
    tipo_evento.create(bind, checkfirst=True)
    resultado_evento.create(bind, checkfirst=True)

    op.create_table(
        "eventos_preservacao",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "id_unidade_acondicionamento",
            sa.Integer(),
            sa.ForeignKey("unidades_acondicionamento.id"),
            nullable=False,
        ),
        sa.Column(
            "tipo_evento",
            sa.Enum(name="tipo_evento_preservacao"),
            nullable=False,
        ),
        sa.Column(
            "resultado",
            sa.Enum(name="resultado_evento_preservacao"),
            nullable=False,
            server_default="sucesso",
        ),
        sa.Column("detalhe", sa.Text(), nullable=True),
        sa.Column("agente", sa.String(length=255), nullable=True),
        sa.Column("correlacao", sa.String(length=255), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_eventos_preservacao_unidade",
        "eventos_preservacao",
        ["id_unidade_acondicionamento"],
    )
    op.create_index(
        "ix_eventos_preservacao_tipo",
        "eventos_preservacao",
        ["tipo_evento"],
    )
    op.create_index(
        "ix_eventos_preservacao_resultado",
        "eventos_preservacao",
        ["resultado"],
    )
    op.create_index(
        "ix_eventos_preservacao_correlacao",
        "eventos_preservacao",
        ["correlacao"],
    )
    op.create_index(
        "ix_eventos_preservacao_criado_em",
        "eventos_preservacao",
        ["criado_em"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_eventos_preservacao_criado_em",
        table_name="eventos_preservacao",
    )
    op.drop_index(
        "ix_eventos_preservacao_correlacao",
        table_name="eventos_preservacao",
    )
    op.drop_index(
        "ix_eventos_preservacao_resultado",
        table_name="eventos_preservacao",
    )
    op.drop_index(
        "ix_eventos_preservacao_tipo",
        table_name="eventos_preservacao",
    )
    op.drop_index(
        "ix_eventos_preservacao_unidade",
        table_name="eventos_preservacao",
    )
    op.drop_table("eventos_preservacao")

    bind = op.get_bind()
    sa.Enum(name="resultado_evento_preservacao").drop(bind, checkfirst=True)
    sa.Enum(name="tipo_evento_preservacao").drop(bind, checkfirst=True)
