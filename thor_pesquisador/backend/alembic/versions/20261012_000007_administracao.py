"""Evolve existing roles without replacing identities or scoped grants."""
from alembic import op
import sqlalchemy as sa

revision = "20261012_000007"
down_revision = "20261011_000006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("papeis", sa.Column("titulo", sa.String(150)))
    op.add_column("papeis", sa.Column("descricao", sa.Text()))
    op.add_column("papeis", sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.execute("UPDATE papeis SET titulo = nome WHERE titulo IS NULL")


def downgrade():
    op.drop_column("papeis", "ativo")
    op.drop_column("papeis", "descricao")
    op.drop_column("papeis", "titulo")
