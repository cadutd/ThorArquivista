"""Paged relational projection of immutable image references (no binaries)."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision = "20261011_000006"
down_revision = "20261011_000005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("publicacao_imagens", sa.Column("referencia", pg.JSONB(), nullable=False, server_default="{}"))


def downgrade():
    op.drop_column("publicacao_imagens", "referencia")
