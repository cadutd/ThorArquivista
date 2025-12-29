"""create unidades de acondicionamento e midias

Revision ID: a85fd65a16e2
Revises:
Create Date: 2025-12-14T19:40:30
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a85fd65a16e2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---- ENUM TYPES (PostgreSQL) ----
    tipo_suporte = sa.Enum("fisico", "digital", "hibrido", name="tipo_suporte")
    tipo_unidade = sa.Enum("caixa", "pasta", "volume", "aip", "sip", "dip", name="tipo_unidade")
    nivel_acesso = sa.Enum("publico", "restrito", "confidencial", name="nivel_acesso")
    status_unidade = sa.Enum("ativa", "inativa", "transferida", "eliminada", name="status_unidade")

    tipo_midia_armazenamento = sa.Enum(
        "filesystem", "nas", "nfs", "lto", "s3", "cloud",
        name="tipo_midia_armazenamento"
    )
    funcao_copia = sa.Enum("preservacao", "backup", "acesso", "quarentena", name="funcao_copia")
    status_copia = sa.Enum("ativa", "indisponivel", "corrompida", "em_verificacao", name="status_copia")

    bind = op.get_bind()
    tipo_suporte.create(bind, checkfirst=True)
    tipo_unidade.create(bind, checkfirst=True)
    nivel_acesso.create(bind, checkfirst=True)
    status_unidade.create(bind, checkfirst=True)
    tipo_midia_armazenamento.create(bind, checkfirst=True)
    funcao_copia.create(bind, checkfirst=True)
    status_copia.create(bind, checkfirst=True)

    # ---- TABELA: unidades_acondicionamento ----
    op.create_table(
        "unidades_acondicionamento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("identificador", sa.String(length=255), nullable=False),
        sa.Column("titulo", sa.String(length=500), nullable=False),
        sa.Column("descricao", sa.String(length=2000), nullable=True),
        sa.Column("tipo_suporte", sa.Enum(name="tipo_suporte"), nullable=False),
        sa.Column("tipo_unidade", sa.Enum(name="tipo_unidade"), nullable=False),
        sa.Column("nivel_acesso", sa.Enum(name="nivel_acesso"), nullable=False, server_default="restrito"),
        sa.Column("status", sa.Enum(name="status_unidade"), nullable=False, server_default="ativa"),
        sa.Column("id_unidade_pai", sa.Integer(), sa.ForeignKey("unidades_acondicionamento.id"), nullable=True),
        sa.Column("id_representa", sa.Integer(), sa.ForeignKey("unidades_acondicionamento.id"), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("identificador", name="uq_unidade_acondicionamento_identificador"),
    )
    op.create_index("ix_unidades_acondicionamento_identificador", "unidades_acondicionamento", ["identificador"])
    op.create_index("ix_unidades_acondicionamento_tipo_suporte", "unidades_acondicionamento", ["tipo_suporte"])
    op.create_index("ix_unidades_acondicionamento_tipo_unidade", "unidades_acondicionamento", ["tipo_unidade"])
    op.create_index("ix_unidades_acondicionamento_nivel_acesso", "unidades_acondicionamento", ["nivel_acesso"])
    op.create_index("ix_unidades_acondicionamento_status", "unidades_acondicionamento", ["status"])

    # ---- TABELA: unidades_acondicionamento_digitais ----
    op.create_table(
        "unidades_acondicionamento_digitais",
        sa.Column(
            "id_unidade_acondicionamento",
            sa.Integer(),
            sa.ForeignKey("unidades_acondicionamento.id"),
            primary_key=True,
        ),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=True),
        sa.Column("status_fixidez", sa.String(length=50), nullable=True),
    )

    # ---- TABELA: midias_armazenamento ----
    op.create_table(
        "midias_armazenamento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("tipo", sa.Enum(name="tipo_midia_armazenamento"), nullable=False),
        sa.Column("descricao", sa.String(length=2000), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("nome", name="uq_midia_armazenamento_nome"),
    )
    op.create_index("ix_midias_armazenamento_nome", "midias_armazenamento", ["nome"])
    op.create_index("ix_midias_armazenamento_tipo", "midias_armazenamento", ["tipo"])
    op.create_index("ix_midias_armazenamento_ativo", "midias_armazenamento", ["ativo"])

    # ---- TABELA: copias_unidades_acondicionamento_digitais ----
    op.create_table(
        "copias_unidades_acondicionamento_digitais",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "id_unidade_acondicionamento",
            sa.Integer(),
            sa.ForeignKey("unidades_acondicionamento.id"),
            nullable=False,
        ),
        sa.Column(
            "id_midia_armazenamento",
            sa.Integer(),
            sa.ForeignKey("midias_armazenamento.id"),
            nullable=False,
        ),
        sa.Column("uri_copia", sa.String(length=1200), nullable=False),
        sa.Column("funcao_copia", sa.Enum(name="funcao_copia"), nullable=False),
        sa.Column("status_copia", sa.Enum(name="status_copia"), nullable=False, server_default="ativa"),
        sa.Column("algoritmo_fixidez", sa.String(length=32), nullable=True),
        sa.Column("hash_fixidez", sa.String(length=128), nullable=True),
        sa.Column("ultima_verificacao_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column("criada_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint(
            "id_unidade_acondicionamento",
            "id_midia_armazenamento",
            "uri_copia",
            name="uq_copia_unidade_acondicionamento_midia_uri",
        ),
    )
    op.create_index(
        "ix_copia_unidade_acondicionamento_funcao",
        "copias_unidades_acondicionamento_digitais",
        ["id_unidade_acondicionamento", "funcao_copia"],
    )


def downgrade() -> None:
    op.drop_index("ix_copia_unidade_acondicionamento_funcao", table_name="copias_unidades_acondicionamento_digitais")
    op.drop_table("copias_unidades_acondicionamento_digitais")

    op.drop_index("ix_midias_armazenamento_ativo", table_name="midias_armazenamento")
    op.drop_index("ix_midias_armazenamento_tipo", table_name="midias_armazenamento")
    op.drop_index("ix_midias_armazenamento_nome", table_name="midias_armazenamento")
    op.drop_table("midias_armazenamento")

    op.drop_table("unidades_acondicionamento_digitais")

    op.drop_index("ix_unidades_acondicionamento_status", table_name="unidades_acondicionamento")
    op.drop_index("ix_unidades_acondicionamento_nivel_acesso", table_name="unidades_acondicionamento")
    op.drop_index("ix_unidades_acondicionamento_tipo_unidade", table_name="unidades_acondicionamento")
    op.drop_index("ix_unidades_acondicionamento_tipo_suporte", table_name="unidades_acondicionamento")
    op.drop_index("ix_unidades_acondicionamento_identificador", table_name="unidades_acondicionamento")
    op.drop_table("unidades_acondicionamento")

    bind = op.get_bind()
    sa.Enum(name="status_copia").drop(bind, checkfirst=True)
    sa.Enum(name="funcao_copia").drop(bind, checkfirst=True)
    sa.Enum(name="tipo_midia_armazenamento").drop(bind, checkfirst=True)

    sa.Enum(name="status_unidade").drop(bind, checkfirst=True)
    sa.Enum(name="nivel_acesso").drop(bind, checkfirst=True)
    sa.Enum(name="tipo_unidade").drop(bind, checkfirst=True)
    sa.Enum(name="tipo_suporte").drop(bind, checkfirst=True)
