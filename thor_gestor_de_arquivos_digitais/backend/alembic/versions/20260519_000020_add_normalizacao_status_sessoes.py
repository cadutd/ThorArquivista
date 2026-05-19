"""add normalization states to submission sessions

Revision ID: 20260519_000020
Revises: 20260519_000019
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op

revision = "20260519_000020"
down_revision = "20260519_000019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'statussessaosubmissao') THEN
                ALTER TYPE statussessaosubmissao ADD VALUE IF NOT EXISTS 'NORMALIZANDO';
                ALTER TYPE statussessaosubmissao ADD VALUE IF NOT EXISTS 'NORMALIZADA';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    pass
