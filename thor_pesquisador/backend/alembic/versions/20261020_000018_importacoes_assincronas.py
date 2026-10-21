"""Durable asynchronous imports; legacy imports remain intact."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "20261020_000018"
down_revision = "20261019_000017"
branch_labels = None
depends_on = None


def upgrade():
    columns = [
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("usuario_id", UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nome_arquivo", sa.String(255), nullable=False), sa.Column("formato", sa.String(12), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=False), sa.Column("bytes_recebidos", sa.BigInteger(), nullable=False),
        sa.Column("checksum", sa.String(64)), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("phase", sa.String(32), nullable=False), sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("geracao", UUID(as_uuid=True)), sa.Column("lease_token", UUID(as_uuid=True)),
        sa.Column("erro", sa.String(255)),
    ]
    for name in ("total", "processados", "fase_processados", "validos", "invalidos"):
        columns.append(sa.Column(name, sa.Integer(), nullable=False))
    for name in ("schema_json", "analise", "configuracao", "relatorio"):
        columns.append(sa.Column(name, JSONB(), nullable=False))
    for name in ("lease_ate", "inicio_fase", "expira_em", "limpo_em", "criado_em", "atualizado_em"):
        columns.append(sa.Column(name, sa.DateTime(timezone=True), nullable=name not in {"expira_em", "criado_em", "atualizado_em"},
                                 server_default=sa.func.now() if name in {"criado_em", "atualizado_em"} else None))
    states = "'RECEBENDO','ANALISANDO','AGUARDANDO_MAPA','VALIDANDO','AGUARDANDO_CONFIRMACAO','ERROS_VALIDACAO','PENDENTE','IMPORTANDO','CONCLUIDA','FALHOU','PAUSADA','CANCELADA','EXPIRADA'"
    columns.append(sa.CheckConstraint("status IN (" + states + ")", name="ck_importacao_async_status"))
    op.create_table("importacoes_assincronas", *columns)
    for name, fields in [
        ("ix_importacao_async_lease", ["status", "lease_ate"]),
        ("ix_importacao_async_usuario_data", ["usuario_id", "instrumento_id", "criado_em"]),
        ("ix_importacao_async_expira", ["expira_em", "limpo_em"]),
        ("ix_importacoes_assincronas_instrumento_id", ["instrumento_id"]),
        ("ix_importacoes_assincronas_usuario_id", ["usuario_id"]),
    ]:
        op.create_index(name, "importacoes_assincronas", fields)
    op.create_table("importacoes_assincronas_partes",
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("importacoes_assincronas.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("categoria", sa.String(12), primary_key=True), sa.Column("numero", sa.Integer(), primary_key=True),
        sa.Column("object_key", sa.String(255), nullable=False), sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("tamanho_bytes", sa.BigInteger(), nullable=False), sa.Column("quantidade", sa.Integer(), nullable=False),
        sa.Column("linhas", sa.Integer(), nullable=False), sa.Column("aplicada", sa.Boolean(), nullable=False),
        sa.Column("erros_key", sa.String(255)), sa.Column("erros_checksum", sa.String(64)))


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM importacoes_assincronas)")):
        raise RuntimeError("Preserve o historico de importacoes assincronas antes de reverter.")
    op.drop_table("importacoes_assincronas_partes")
    op.drop_table("importacoes_assincronas")
