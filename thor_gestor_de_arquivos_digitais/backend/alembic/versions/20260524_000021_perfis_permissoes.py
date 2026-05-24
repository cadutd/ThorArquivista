"""create profiles and permissions

Revision ID: 20260524_000021
Revises: 20260519_000020
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op

revision = "20260524_000021"
down_revision = "20260519_000020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS permissoes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            codigo VARCHAR(150) NOT NULL,
            nome VARCHAR(255) NOT NULL,
            descricao TEXT,
            modulo VARCHAR(100) NOT NULL,
            funcao VARCHAR(100) NOT NULL,
            acao VARCHAR(20) NOT NULL,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_permissoes_codigo UNIQUE (codigo),
            CONSTRAINT uq_permissoes_funcao_acao UNIQUE (funcao, acao),
            CONSTRAINT ck_permissoes_acao CHECK (acao IN ('CRIAR', 'EDITAR', 'CONSULTAR', 'EXCLUIR'))
        );

        CREATE TABLE IF NOT EXISTS perfis (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            codigo VARCHAR(80) NOT NULL,
            nome VARCHAR(150) NOT NULL,
            descricao TEXT,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,
            sistema BOOLEAN NOT NULL DEFAULT FALSE,
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_perfis_codigo UNIQUE (codigo),
            CONSTRAINT uq_perfis_nome UNIQUE (nome)
        );

        CREATE TABLE IF NOT EXISTS perfil_permissao (
            perfil_id UUID NOT NULL REFERENCES perfis(id) ON DELETE CASCADE,
            permissao_id UUID NOT NULL REFERENCES permissoes(id) ON DELETE CASCADE,
            PRIMARY KEY (perfil_id, permissao_id)
        );

        ALTER TABLE usuarios
            ADD COLUMN IF NOT EXISTS id_perfil UUID REFERENCES perfis(id) ON DELETE SET NULL;

        CREATE INDEX IF NOT EXISTS ix_permissoes_codigo ON permissoes (codigo);
        CREATE INDEX IF NOT EXISTS ix_permissoes_nome ON permissoes (nome);
        CREATE INDEX IF NOT EXISTS ix_permissoes_modulo ON permissoes (modulo);
        CREATE INDEX IF NOT EXISTS ix_permissoes_funcao ON permissoes (funcao);
        CREATE INDEX IF NOT EXISTS ix_permissoes_acao ON permissoes (acao);
        CREATE INDEX IF NOT EXISTS ix_permissoes_ativo ON permissoes (ativo);
        CREATE INDEX IF NOT EXISTS ix_perfis_codigo ON perfis (codigo);
        CREATE INDEX IF NOT EXISTS ix_perfis_nome ON perfis (nome);
        CREATE INDEX IF NOT EXISTS ix_perfis_ativo ON perfis (ativo);
        CREATE INDEX IF NOT EXISTS ix_perfis_sistema ON perfis (sistema);
        CREATE INDEX IF NOT EXISTS ix_usuarios_id_perfil ON usuarios (id_perfil);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE usuarios DROP COLUMN IF EXISTS id_perfil;
        DROP TABLE IF EXISTS perfil_permissao;
        DROP TABLE IF EXISTS perfis;
        DROP TABLE IF EXISTS permissoes;
        """
    )
