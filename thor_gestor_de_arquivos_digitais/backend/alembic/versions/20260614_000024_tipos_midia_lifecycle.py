"""tipos de midia e ciclo de vida

Revision ID: 20260614_000024
Revises: 20260524_000023
Create Date: 2026-06-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260614_000024"
down_revision = "20260524_000023"
branch_labels = None
depends_on = None


TIPOS = [
    ("00000000-0000-0000-0000-000000000101", "FILESYSTEM", "Sistema de arquivos", 5, 6),
    ("00000000-0000-0000-0000-000000000102", "NAS", "Network attached storage", 5, 6),
    ("00000000-0000-0000-0000-000000000103", "NFS", "Network file system", 5, 6),
    ("00000000-0000-0000-0000-000000000104", "LTO", "Fita LTO", 10, 12),
    ("00000000-0000-0000-0000-000000000105", "S3", "Armazenamento S3", 10, 12),
    ("00000000-0000-0000-0000-000000000106", "CLOUD", "Armazenamento em nuvem", 10, 12),
]


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.create_table(
        "tipos_midia_armazenamento",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("tempo_duracao_anos", sa.Integer(), nullable=False),
        sa.Column("periodicidade_checagem_meses", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome", name="uq_tipos_midia_armazenamento_nome"),
    )
    op.create_index("ix_tipos_midia_armazenamento_nome", "tipos_midia_armazenamento", ["nome"])
    op.create_index("ix_tipos_midia_armazenamento_ativo", "tipos_midia_armazenamento", ["ativo"])

    for tipo_id, nome, descricao, duracao, periodicidade in TIPOS:
        op.execute(
            sa.text(
                """
                INSERT INTO tipos_midia_armazenamento
                    (id, nome, descricao, tempo_duracao_anos, periodicidade_checagem_meses, ativo)
                VALUES
                    (CAST(:id AS uuid), :nome, :descricao, :duracao, :periodicidade, true)
                ON CONFLICT (nome) DO NOTHING
                """
            ).bindparams(
                id=tipo_id,
                nome=nome,
                descricao=descricao,
                duracao=duracao,
                periodicidade=periodicidade,
            )
        )

    op.add_column("midias_armazenamento", sa.Column("tipo_midia_id", sa.UUID(), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("data_aquisicao", sa.Date(), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("data_inicio_uso", sa.Date(), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("data_validade", sa.Date(), nullable=True))
    op.add_column(
        "midias_armazenamento",
        sa.Column("ultima_checagem_integridade", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "midias_armazenamento",
        sa.Column("proxima_checagem_integridade", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("midias_armazenamento", sa.Column("capacidade_total_bytes", sa.BigInteger(), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("capacidade_utilizada_bytes", sa.BigInteger(), nullable=True))
    op.add_column("midias_armazenamento", sa.Column("identificador_fisico", sa.String(length=255), nullable=True))
    op.add_column(
        "midias_armazenamento",
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.execute(
        """
        UPDATE midias_armazenamento
           SET tipo_midia_id = CASE tipo::text
                WHEN 'FILESYSTEM' THEN '00000000-0000-0000-0000-000000000101'::uuid
                WHEN 'NAS' THEN '00000000-0000-0000-0000-000000000102'::uuid
                WHEN 'NFS' THEN '00000000-0000-0000-0000-000000000103'::uuid
                WHEN 'LTO' THEN '00000000-0000-0000-0000-000000000104'::uuid
                WHEN 'S3' THEN '00000000-0000-0000-0000-000000000105'::uuid
                WHEN 'CLOUD' THEN '00000000-0000-0000-0000-000000000106'::uuid
                ELSE '00000000-0000-0000-0000-000000000101'::uuid
           END
         WHERE tipo_midia_id IS NULL
        """
    )

    op.alter_column("midias_armazenamento", "tipo_midia_id", nullable=False)
    op.create_foreign_key(
        "fk_midias_armazenamento_tipo_midia_id",
        "midias_armazenamento",
        "tipos_midia_armazenamento",
        ["tipo_midia_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_midias_armazenamento_tipo_midia_id", "midias_armazenamento", ["tipo_midia_id"])
    op.create_index("ix_midias_armazenamento_data_validade", "midias_armazenamento", ["data_validade"])
    op.create_index(
        "ix_midias_armazenamento_proxima_checagem_integridade",
        "midias_armazenamento",
        ["proxima_checagem_integridade"],
    )
    op.create_index(
        "ix_midias_armazenamento_identificador_fisico",
        "midias_armazenamento",
        ["identificador_fisico"],
    )

    op.drop_index("ix_midias_armazenamento_tipo", table_name="midias_armazenamento")
    op.drop_column("midias_armazenamento", "tipo")


def downgrade() -> None:
    op.add_column(
        "midias_armazenamento",
        sa.Column("tipo", sa.Enum("FILESYSTEM", "NAS", "NFS", "LTO", "S3", "CLOUD", name="tipo_midia_armazenamento"), nullable=True),
    )
    op.execute(
        """
        UPDATE midias_armazenamento m
           SET tipo = CASE t.nome
                WHEN 'FILESYSTEM' THEN 'FILESYSTEM'::tipo_midia_armazenamento
                WHEN 'NAS' THEN 'NAS'::tipo_midia_armazenamento
                WHEN 'NFS' THEN 'NFS'::tipo_midia_armazenamento
                WHEN 'LTO' THEN 'LTO'::tipo_midia_armazenamento
                WHEN 'S3' THEN 'S3'::tipo_midia_armazenamento
                WHEN 'CLOUD' THEN 'CLOUD'::tipo_midia_armazenamento
                ELSE 'FILESYSTEM'::tipo_midia_armazenamento
           END
          FROM tipos_midia_armazenamento t
         WHERE m.tipo_midia_id = t.id
        """
    )
    op.execute(
        "UPDATE midias_armazenamento SET tipo = 'FILESYSTEM'::tipo_midia_armazenamento WHERE tipo IS NULL"
    )
    op.alter_column("midias_armazenamento", "tipo", nullable=False)
    op.create_index("ix_midias_armazenamento_tipo", "midias_armazenamento", ["tipo"])

    op.drop_index("ix_midias_armazenamento_identificador_fisico", table_name="midias_armazenamento")
    op.drop_index("ix_midias_armazenamento_proxima_checagem_integridade", table_name="midias_armazenamento")
    op.drop_index("ix_midias_armazenamento_data_validade", table_name="midias_armazenamento")
    op.drop_index("ix_midias_armazenamento_tipo_midia_id", table_name="midias_armazenamento")
    op.drop_constraint("fk_midias_armazenamento_tipo_midia_id", "midias_armazenamento", type_="foreignkey")
    op.drop_column("midias_armazenamento", "atualizado_em")
    op.drop_column("midias_armazenamento", "identificador_fisico")
    op.drop_column("midias_armazenamento", "capacidade_utilizada_bytes")
    op.drop_column("midias_armazenamento", "capacidade_total_bytes")
    op.drop_column("midias_armazenamento", "proxima_checagem_integridade")
    op.drop_column("midias_armazenamento", "ultima_checagem_integridade")
    op.drop_column("midias_armazenamento", "data_validade")
    op.drop_column("midias_armazenamento", "data_inicio_uso")
    op.drop_column("midias_armazenamento", "data_aquisicao")
    op.drop_column("midias_armazenamento", "tipo_midia_id")

    op.drop_index("ix_tipos_midia_armazenamento_ativo", table_name="tipos_midia_armazenamento")
    op.drop_index("ix_tipos_midia_armazenamento_nome", table_name="tipos_midia_armazenamento")
    op.drop_table("tipos_midia_armazenamento")
