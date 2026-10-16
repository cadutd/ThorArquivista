"""Recoverable export-prefix cleanup watermark."""
from alembic import op

revision = "20261015_000012"
down_revision = "20261015_000011"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE exportacoes ADD COLUMN IF NOT EXISTS ultimo_descarte_em TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_exportacoes_ultimo_descarte_em ON exportacoes (ultimo_descarte_em)")


def downgrade():
    op.drop_index("ix_exportacoes_ultimo_descarte_em", table_name="exportacoes")
    op.drop_column("exportacoes", "ultimo_descarte_em")
