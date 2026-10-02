"""busca avancada

Revision ID: 20261002_000002
Revises: 20261002_000001
Create Date: 2026-10-02
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261002_000002"
down_revision = "20261002_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("instrumento_campos", sa.Column("filtro_avancado", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("instrumento_campos", sa.Column("facetavel", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("instrumento_campos", sa.Column("ordenavel", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    op.create_table(
        "indexacao_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("instrumento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("instrumentos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), server_default="PENDENTE", nullable=False),
        sa.Column("total_estimado", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processados", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ultimo_cursor_mongodb", sa.String(255), nullable=True),
        sa.Column("erro", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_indexacao_jobs_instrumento", "indexacao_jobs", ["instrumento_id"])
    op.create_index("ix_indexacao_jobs_status", "indexacao_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("indexacao_jobs")
    op.drop_column("instrumento_campos", "ordenavel")
    op.drop_column("instrumento_campos", "facetavel")
    op.drop_column("instrumento_campos", "filtro_avancado")
