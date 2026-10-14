"""Editorial controls and scoped access; no implicit publication or elevation."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "20261011_000004"
down_revision = "20261003_000003"
branch_labels = None
depends_on = None


def upgrade():
    for name, default in [("versao_editorial", "1"), ("geracao_publica", "0"), ("geracao_indexada", "-1")]:
        op.add_column("instrumentos", sa.Column(name, sa.Integer(), nullable=False, server_default=default))
    op.add_column("instrumentos", sa.Column("publicacao_id", pg.UUID(as_uuid=True)))
    op.add_column("instrumento_campos", sa.Column("exibir_publico", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("indexacao_jobs", sa.Column("geracao_publica", sa.Integer()))
    op.create_unique_constraint("uq_job_publico_geracao", "indexacao_jobs", ["instrumento_id", "geracao_publica"])
    op.create_table("papeis", sa.Column("nome", sa.String(40), primary_key=True), sa.Column("permissoes", pg.JSONB(), nullable=False))
    op.bulk_insert(sa.table("papeis", sa.column("nome", sa.String), sa.column("permissoes", pg.JSONB)), [
        {"nome": "ADMIN", "permissoes": ["*"]},
        {"nome": "GESTOR_INSTRUMENTOS", "permissoes": ["consultar", "criar_instrumento", "gerenciar", "editar_registro", "enviar_revisao", "publicar", "arquivar", "reindexar", "gerenciar_imagens"]},
        {"nome": "EDITOR", "permissoes": ["consultar", "editar_registro", "enviar_revisao", "gerenciar_imagens"]},
        {"nome": "REVISOR", "permissoes": ["consultar", "revisar"]},
        {"nome": "CONSULTA_INTERNA", "permissoes": ["consultar"]},
        {"nome": "PUBLICO_AUTENTICADO", "permissoes": ["consulta_publicada"]},
    ])
    op.create_table("acessos_instrumento",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("usuario_id", pg.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("papel", sa.String(40), sa.ForeignKey("papeis.nome"), nullable=False),
        sa.Column("instrumento_id", pg.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="CASCADE")),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    for col in ["usuario_id", "instrumento_id"]:
        op.create_index("ix_acessos_instrumento_" + col, "acessos_instrumento", [col])
    op.create_index("uq_acesso_escopo", "acessos_instrumento", ["usuario_id", "papel", "instrumento_id"], unique=True, postgresql_where=sa.text("instrumento_id IS NOT NULL"))
    op.create_index("uq_acesso_global", "acessos_instrumento", ["usuario_id", "papel"], unique=True, postgresql_where=sa.text("instrumento_id IS NULL"))
    op.create_table("editorial_registros",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", pg.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("registro_id", sa.String(255), nullable=False),
        sa.Column("status_editorial", sa.String(40), nullable=False, server_default="RASCUNHO"),
        sa.Column("status_operacional", sa.String(40), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("versao_publicada", sa.Integer()),
        sa.Column("snapshot_id", sa.String(255)),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("instrumento_id", "registro_id", name="uq_editorial_registro"))
    for col in ["instrumento_id", "status_editorial"]:
        op.create_index("ix_editorial_registros_" + col, "editorial_registros", [col])
    op.create_table("publicacoes_instrumento",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", pg.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("schema_json", pg.JSONB(), nullable=False),
        sa.Column("usuario_id", pg.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("instrumento_id", "versao", name="uq_publicacao_instrumento"))
    op.create_index("ix_publicacoes_instrumento_instrumento_id", "publicacoes_instrumento", ["instrumento_id"])
    op.create_table("eventos_editoriais",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("registro_id", sa.String(255)),
        sa.Column("usuario_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("agente", sa.String(255), nullable=False),
        sa.Column("acao", sa.String(40), nullable=False),
        sa.Column("estado_anterior", sa.String(40), nullable=False),
        sa.Column("estado_novo", sa.String(40), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False),
        sa.Column("justificativa", sa.String(4000)),
        sa.Column("resultado", pg.JSONB(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    for col in ["instrumento_id", "criado_em"]:
        op.create_index("ix_eventos_editoriais_" + col, "eventos_editoriais", [col])


def downgrade():
    for table in ["eventos_editoriais", "publicacoes_instrumento", "editorial_registros", "acessos_instrumento", "papeis"]:
        op.drop_table(table)
    op.drop_constraint("uq_job_publico_geracao", "indexacao_jobs")
    op.drop_column("indexacao_jobs", "geracao_publica")
    op.drop_column("instrumento_campos", "exibir_publico")
    for col in ["publicacao_id", "versao_editorial", "geracao_publica", "geracao_indexada"]:
        op.drop_column("instrumentos", col)
