"""Optional institutional card covers, separate from protected record images."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261019_000016"
down_revision = "20261016_000015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("instrumento_capas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("object_key", sa.String(255), nullable=False, unique=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=False),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("criado_por", postgresql.UUID(as_uuid=True), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.add_column("instrumentos", sa.Column("imagem_card_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key("fk_instrumento_capa", "instrumentos", "instrumento_capas", ["imagem_card_id"], ["id"])


def downgrade():
    if op.get_bind().scalar(sa.text("SELECT EXISTS (SELECT 1 FROM instrumento_capas)")):
        raise RuntimeError("Preserve as capas e referencias historicas antes de reverter esta migration.")
    op.drop_constraint("fk_instrumento_capa", "instrumentos", type_="foreignkey")
    op.drop_column("instrumentos", "imagem_card_id")
    op.drop_table("instrumento_capas")
