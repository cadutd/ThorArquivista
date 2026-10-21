"""Resumable imports; source files and row payloads are not retained in SQL."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261019_000017"
down_revision = "20261019_000016"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("importacoes_registros",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("usuario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assinatura", sa.String(64), nullable=False),
        sa.Column("configuracao", postgresql.JSONB(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("processados", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('EM_ANDAMENTO','INTERROMPIDA','CONCLUIDA')", name="ck_importacao_status"))
    op.create_index("ix_importacoes_registros_instrumento_id", "importacoes_registros", ["instrumento_id"])
    op.create_index("ix_importacoes_registros_usuario_id", "importacoes_registros", ["usuario_id"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM importacoes_registros)")):
        raise RuntimeError("Preserve o historico de importacoes antes de reverter esta migration.")
    op.drop_table("importacoes_registros")
