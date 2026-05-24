"""remove legacy operator user role

Revision ID: 20260524_000023
Revises: 20260524_000022
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op

revision = "20260524_000023"
down_revision = "20260524_000022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE usuarios SET papel = 'ARQUIVISTA' WHERE papel = 'OPERADOR';
        UPDATE usuarios u
           SET id_perfil = p_arq.id
          FROM perfis p_old, perfis p_arq
         WHERE p_old.codigo = 'OPERADOR'
           AND p_arq.codigo = 'ARQUIVISTA'
           AND u.id_perfil = p_old.id;
        DELETE FROM perfil_permissao WHERE perfil_id IN (SELECT id FROM perfis WHERE codigo = 'OPERADOR');
        DELETE FROM perfis WHERE codigo = 'OPERADOR';
        ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS ck_usuarios_papel;
        ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_papel
            CHECK (papel IN ('ADMIN', 'ARQUIVISTA', 'ADMISSAO', 'GESTOR_ARMAZENAMENTO', 'CONSULTA'));
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS ck_usuarios_papel;
        ALTER TABLE usuarios ADD CONSTRAINT ck_usuarios_papel
            CHECK (papel IN ('ADMIN', 'ARQUIVISTA', 'ADMISSAO', 'GESTOR_ARMAZENAMENTO', 'CONSULTA', 'OPERADOR'));
        """
    )
