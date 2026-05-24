"""allow new user profile legacy codes

Revision ID: 20260524_000022
Revises: 20260524_000021
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op

revision = "20260524_000022"
down_revision = "20260524_000021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS ck_usuarios_papel;
        ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_papel
            CHECK (papel IN ('ADMIN', 'ARQUIVISTA', 'ADMISSAO', 'GESTOR_ARMAZENAMENTO', 'CONSULTA', 'OPERADOR'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE usuarios
           SET papel = 'OPERADOR'
         WHERE papel IN ('ADMISSAO', 'GESTOR_ARMAZENAMENTO');
        ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS ck_usuarios_papel;
        ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_papel
            CHECK (papel IN ('ADMIN', 'ARQUIVISTA', 'OPERADOR', 'CONSULTA'));
        """
    )
