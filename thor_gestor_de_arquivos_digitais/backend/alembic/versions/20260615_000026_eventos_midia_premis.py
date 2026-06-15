"""eventos premis de midia de armazenamento

Revision ID: 20260615_000026
Revises: 20260615_000025
Create Date: 2026-06-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260615_000026"
down_revision = "20260615_000025"
branch_labels = None
depends_on = None


TIPOS_EVENTO_MIDIA = (
    "CRIACAO_MIDIA",
    "ATUALIZACAO_MIDIA",
    "CHECAGEM_MIDIA",
    "MIGRACAO_MIDIA",
    "DESATIVACAO_MIDIA",
    "VALIDADE_EXPIRADA",
    "FALHA_INTEGRIDADE",
    "ALERTA_INTEGRIDADE",
)


def upgrade() -> None:
    tipo_evento_midia = postgresql.ENUM(
        *TIPOS_EVENTO_MIDIA,
        name="tipo_evento_midia_armazenamento",
    )
    tipo_evento_midia.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "eventos_midia_armazenamento",
        sa.Column("data_evento", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
    )
    op.add_column(
        "eventos_midia_armazenamento",
        sa.Column("premis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "eventos_midia_armazenamento",
        sa.Column("evento_relacionado_id", sa.Integer(), nullable=True),
    )

    op.execute(
        """
        UPDATE eventos_midia_armazenamento
           SET data_evento = criado_em
         WHERE data_evento IS NULL
        """
    )

    op.execute(
        """
        ALTER TABLE eventos_midia_armazenamento
        ALTER COLUMN tipo_evento TYPE tipo_evento_midia_armazenamento
        USING (
            CASE
                WHEN detalhe ILIKE '%cadastrad%' THEN 'CRIACAO_MIDIA'
                WHEN detalhe ILIKE '%desativ%' THEN 'DESATIVACAO_MIDIA'
                WHEN tipo_evento::text = 'MIGRACAO' THEN 'MIGRACAO_MIDIA'
                WHEN tipo_evento::text = 'FIXIDEZ' THEN 'CHECAGEM_MIDIA'
                ELSE 'ATUALIZACAO_MIDIA'
            END
        )::tipo_evento_midia_armazenamento
        """
    )

    op.execute(
        """
        UPDATE eventos_midia_armazenamento
           SET premis_json = jsonb_build_object(
                'eventType', tipo_evento::text,
                'eventDateTime', to_char(data_evento AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
                'eventDetail', detalhe,
                'eventOutcomeInformation', jsonb_build_object(
                    'eventOutcome', resultado::text,
                    'eventOutcomeDetail', COALESCE(detalhe, resultado::text)
                ),
                'linkingAgentIdentifier', jsonb_build_object(
                    'linkingAgentIdentifierType', 'usuario',
                    'linkingAgentIdentifierValue', agente
                ),
                'linkingObjectIdentifier', jsonb_build_object(
                    'linkingObjectIdentifierType', 'midia_armazenamento',
                    'linkingObjectIdentifierValue', id_midia_armazenamento::text
                )
           )
         WHERE premis_json IS NULL
        """
    )

    op.alter_column("eventos_midia_armazenamento", "data_evento", nullable=False)
    op.create_foreign_key(
        "fk_eventos_midia_armazenamento_evento_relacionado",
        "eventos_midia_armazenamento",
        "eventos_midia_armazenamento",
        ["evento_relacionado_id"],
        ["id"],
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_data_evento",
        "eventos_midia_armazenamento",
        ["data_evento"],
    )
    op.create_index(
        "ix_eventos_midia_armazenamento_evento_relacionado_id",
        "eventos_midia_armazenamento",
        ["evento_relacionado_id"],
    )


def downgrade() -> None:
    tipo_evento_preservacao = postgresql.ENUM(
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

    op.drop_index("ix_eventos_midia_armazenamento_evento_relacionado_id", table_name="eventos_midia_armazenamento")
    op.drop_index("ix_eventos_midia_armazenamento_data_evento", table_name="eventos_midia_armazenamento")
    op.drop_constraint(
        "fk_eventos_midia_armazenamento_evento_relacionado",
        "eventos_midia_armazenamento",
        type_="foreignkey",
    )

    op.execute(
        """
        ALTER TABLE eventos_midia_armazenamento
        ALTER COLUMN tipo_evento TYPE tipo_evento_preservacao
        USING (
            CASE
                WHEN tipo_evento::text = 'MIGRACAO_MIDIA' THEN 'MIGRACAO'
                WHEN tipo_evento::text IN ('CHECAGEM_MIDIA', 'FALHA_INTEGRIDADE', 'ALERTA_INTEGRIDADE') THEN 'FIXIDEZ'
                ELSE 'OUTRO'
            END
        )::tipo_evento_preservacao
        """
    )

    op.drop_column("eventos_midia_armazenamento", "evento_relacionado_id")
    op.drop_column("eventos_midia_armazenamento", "premis_json")
    op.drop_column("eventos_midia_armazenamento", "data_evento")

    postgresql.ENUM(name="tipo_evento_midia_armazenamento").drop(op.get_bind(), checkfirst=True)
