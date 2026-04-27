"""allow EAD2002 archival description norm

Revision ID: 20260427_000005
Revises: 20260426_000004
Create Date: 2026-04-27
"""

from __future__ import annotations

from alembic import op

revision = "20260427_000005"
down_revision = "20260426_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE registros_descritivos
        DROP CONSTRAINT IF EXISTS ck_registro_descritivo_norma;

        ALTER TABLE registros_descritivos
        ADD CONSTRAINT ck_registro_descritivo_norma
        CHECK (norma IN ('NOBRADE','ISAD_G','EAD2002'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE registros_descritivos
        SET norma = 'ISAD_G'
        WHERE norma = 'EAD2002';

        ALTER TABLE registros_descritivos
        DROP CONSTRAINT IF EXISTS ck_registro_descritivo_norma;

        ALTER TABLE registros_descritivos
        ADD CONSTRAINT ck_registro_descritivo_norma
        CHECK (norma IN ('NOBRADE','ISAD_G'));
        """
    )
