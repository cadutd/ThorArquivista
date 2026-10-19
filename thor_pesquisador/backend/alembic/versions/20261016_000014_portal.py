"""Consultive identities, institutional theme and bounded daily access counters."""
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261016_000014"
down_revision = "20261015_000013"
branch_labels = None
depends_on = None

COLORS = {"primaria": "#0e6496", "secundaria": "#235347", "destaque": "#8f2453",
          "fundo": "#ffffff", "texto": "#17232d"}


def upgrade():
    op.alter_column("sessoes", "usuario_id", nullable=True)
    op.add_column("sessoes", sa.Column("cpf_consultivo", sa.String(11)))
    op.add_column("sessoes", sa.Column("nome_consultivo", sa.String(255)))
    op.create_check_constraint("ck_sessao_identidade", "sessoes", "usuario_id IS NOT NULL OR cpf_consultivo IS NOT NULL")
    op.create_table("configuracao_portal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome_instituicao", sa.String(150), nullable=False),
        sa.Column("cores", postgresql.JSONB(), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("id = 1", name="ck_portal_singleton"))
    table = sa.table("configuracao_portal", sa.column("id"), sa.column("nome_instituicao"),
                     sa.column("cores", postgresql.JSONB()), sa.column("versao"))
    op.bulk_insert(table, [dict(id=1, nome_instituicao="Thor Pesquisador", cores=COLORS, versao=1)])
    op.create_table("portal_acessos",
        sa.Column("sessao_chave", sa.String(64), primary_key=True),
        sa.Column("instrumento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dia", sa.Date(), primary_key=True))
    op.create_index("ix_portal_acessos_dia_instrumento", "portal_acessos", ["dia", "instrumento_id"])
    # ADMIN already has wildcard. No grant to custom profiles or scoped operators.


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM sessoes WHERE usuario_id IS NULL)")):
        raise RuntimeError("Revogue/expire as sessoes consultivas pelo procedimento documentado antes do downgrade.")
    # Remove only permissions introduced by this revision, preserving all other profile values.
    for code in ("portal_configuracao_consultar", "portal_configuracao_editar"):
        op.execute(sa.text("UPDATE papeis SET permissoes = permissoes - :code WHERE permissoes ? :code").bindparams(code=code))
    op.drop_table("portal_acessos")
    op.drop_table("configuracao_portal")
    op.drop_constraint("ck_sessao_identidade", "sessoes")
    op.drop_column("sessoes", "nome_consultivo")
    op.drop_column("sessoes", "cpf_consultivo")
    op.alter_column("sessoes", "usuario_id", nullable=False)
