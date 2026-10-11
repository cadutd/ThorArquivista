"""Optional document images, links and audit history."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "20261003_000003"
down_revision = "20261002_000002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "imagens_documento",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("descricao", sa.Text()),
        sa.Column("tipo_referencia", sa.String(40), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("object_key", sa.String(255), unique=True),
        sa.Column("thumbnail_key", sa.String(255)),
        sa.Column("thumbnail_uri", sa.Text()),
        sa.Column("manifest_iiif_uri", sa.Text()),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("tamanho_bytes", sa.BigInteger()),
        sa.Column("largura", sa.Integer()),
        sa.Column("altura", sa.Integer()),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column("direitos_acesso", sa.String(40), nullable=False),
        sa.Column("metadados_json", pg.JSONB(), nullable=False, server_default="{}"),
        sa.Column("criado_por", pg.UUID(as_uuid=True), sa.ForeignKey("usuarios.id", ondelete="SET NULL")),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("tipo_referencia IN ('UPLOAD','URL','IIIF','REPOSITORIO_EXTERNO')", name="ck_imagem_referencia"),
        sa.CheckConstraint("direitos_acesso IN ('PUBLICO','INTERNO','RESTRITO')", name="ck_imagem_acesso"),
    )
    for column in ["titulo", "direitos_acesso", "criado_em"]:
        op.create_index(f"ix_imagens_documento_{column}", "imagens_documento", [column])
    op.create_table(
        "registro_imagens",
        sa.Column("instrumento_id", pg.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("registro_id", sa.String(255), primary_key=True),
        sa.Column("imagem_id", pg.UUID(as_uuid=True), sa.ForeignKey("imagens_documento.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("principal", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("legenda", sa.Text()),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("ordem >= 0", name="ck_registro_imagem_ordem"),
    )
    op.create_index("ix_registro_imagens_registro", "registro_imagens", ["instrumento_id", "registro_id", "ordem"])
    op.create_index("ix_registro_imagens_imagem_id", "registro_imagens", ["imagem_id"])
    op.create_index("uq_registro_imagens_principal", "registro_imagens", ["instrumento_id", "registro_id"], unique=True, postgresql_where=sa.text("principal"))
    op.create_table(
        "auditoria_imagens",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("imagem_id", pg.UUID(as_uuid=True)),
        sa.Column("instrumento_id", pg.UUID(as_uuid=True)),
        sa.Column("registro_id", sa.String(255)),
        sa.Column("usuario_id", pg.UUID(as_uuid=True)),
        sa.Column("acao", sa.String(60), nullable=False),
        sa.Column("detalhe", pg.JSONB(), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auditoria_imagens_imagem_id", "auditoria_imagens", ["imagem_id"])


def downgrade():
    op.drop_table("auditoria_imagens")
    op.drop_table("registro_imagens")
    op.drop_table("imagens_documento")
