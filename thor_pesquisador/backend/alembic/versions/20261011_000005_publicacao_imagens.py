"""Preserve published image references, including links removed from drafts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "20261011_000005"
down_revision = "20261011_000004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("editorial_registros", sa.Column("aprovacao_hash", sa.String(64)))
    op.create_table("publicacao_imagens",
        sa.Column("snapshot_id", sa.String(255), primary_key=True),
        sa.Column("imagem_id", pg.UUID(as_uuid=True), sa.ForeignKey("imagens_documento.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("instrumento_id", pg.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="RESTRICT"), nullable=False))
    op.create_index("ix_publicacao_imagens_instrumento_id", "publicacao_imagens", ["instrumento_id"])
    op.create_index("ix_publicacao_imagens_imagem_id", "publicacao_imagens", ["imagem_id"])


def downgrade():
    op.drop_table("publicacao_imagens")
    op.drop_column("editorial_registros", "aprovacao_hash")
