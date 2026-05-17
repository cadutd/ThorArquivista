"""create local users profile table

Revision ID: 20260517_000015
Revises: 20260516_000014
Create Date: 2026-05-17
"""

from __future__ import annotations

from alembic import op

revision = "20260517_000015"
down_revision = "20260516_000014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            keycloak_sub VARCHAR(255),
            username VARCHAR(150) NOT NULL,
            nome VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            papel VARCHAR(50) NOT NULL DEFAULT 'OPERADOR',
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            observacoes TEXT,
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_usuarios_keycloak_sub UNIQUE (keycloak_sub),
            CONSTRAINT uq_usuarios_username UNIQUE (username),
            CONSTRAINT uq_usuarios_email UNIQUE (email),
            CONSTRAINT ck_usuarios_papel CHECK (papel IN ('ADMIN', 'ARQUIVISTA', 'OPERADOR', 'CONSULTA'))
        );

        CREATE INDEX IF NOT EXISTS ix_usuarios_keycloak_sub ON usuarios (keycloak_sub);
        CREATE INDEX IF NOT EXISTS ix_usuarios_username ON usuarios (username);
        CREATE INDEX IF NOT EXISTS ix_usuarios_nome ON usuarios (nome);
        CREATE INDEX IF NOT EXISTS ix_usuarios_email ON usuarios (email);
        CREATE INDEX IF NOT EXISTS ix_usuarios_papel ON usuarios (papel);
        CREATE INDEX IF NOT EXISTS ix_usuarios_ativo ON usuarios (ativo);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS usuarios;")
