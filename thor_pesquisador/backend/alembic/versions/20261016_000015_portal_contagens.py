"""Daily aggregates keep the public ranking independent of visitor volume."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261016_000015"
down_revision = "20261016_000014"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("portal_contagens",
        sa.Column("instrumento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dia", sa.Date(), primary_key=True),
        sa.Column("quantidade", sa.BigInteger(), nullable=False))
    op.create_index("ix_portal_contagens_dia", "portal_contagens", ["dia"])
    op.execute("INSERT INTO portal_contagens(instrumento_id,dia,quantidade) SELECT instrumento_id,dia,count(*) FROM portal_acessos GROUP BY instrumento_id,dia")


def downgrade():
    op.drop_table("portal_contagens")
