"""remove legacy fields from submission sessions

Revision ID: 20260519_000019
Revises: 20260518_000018
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260519_000019"
down_revision = "20260518_000018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sessoes_submissao") as batch_op:
        batch_op.drop_column("protocolo_transferencia")
        batch_op.drop_column("quantidade_itens_informada")
        batch_op.drop_column("quantidade_itens_recebida")


def downgrade() -> None:
    with op.batch_alter_table("sessoes_submissao") as batch_op:
        batch_op.add_column(sa.Column("protocolo_transferencia", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("quantidade_itens_informada", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("quantidade_itens_recebida", sa.Integer(), nullable=True))
