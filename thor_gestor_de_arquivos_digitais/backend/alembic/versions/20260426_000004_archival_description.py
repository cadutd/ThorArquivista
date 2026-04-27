"""archival description

Revision ID: 20260426_000004
Revises: 20260426_000003
Create Date: 2026-04-26
"""

from __future__ import annotations

from alembic import op

revision = "20260426_000004"
down_revision = "20260426_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        r"""
        CREATE EXTENSION IF NOT EXISTS pgcrypto;

        CREATE TABLE IF NOT EXISTS registros_descritivos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            parent_id UUID REFERENCES registros_descritivos(id) ON DELETE CASCADE,
            nivel VARCHAR(10) NOT NULL,
            norma VARCHAR(20) NOT NULL DEFAULT 'NOBRADE',
            codigo_referencia VARCHAR(255) NOT NULL,
            titulo VARCHAR(500) NOT NULL,
            data_inicial DATE,
            data_final DATE,
            dimensao VARCHAR(255),
            suporte VARCHAR(255),
            produtor VARCHAR(500),
            historia_administrativa TEXT,
            historia_arquivistica TEXT,
            procedencia TEXT,
            ambito_conteudo TEXT,
            avaliacao_eliminacao TEXT,
            incorporacoes TEXT,
            sistema_arranjo TEXT,
            condicoes_acesso TEXT,
            condicoes_reproducao TEXT,
            idioma VARCHAR(255),
            caracteristicas_tecnicas TEXT,
            originais TEXT,
            copias TEXT,
            unidades_relacionadas TEXT,
            publicacoes TEXT,
            notas TEXT,
            arquivista_responsavel VARCHAR(255),
            regras_convencoes TEXT,
            data_descricao TIMESTAMPTZ,
            assuntos TEXT,
            pessoas TEXT,
            locais TEXT,
            entidades TEXT,
            eventos TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            CONSTRAINT ck_registro_descritivo_nivel CHECK (nivel IN ('1','2','2.5','3','3.5','4','5')),
            CONSTRAINT ck_registro_descritivo_norma CHECK (norma IN ('NOBRADE','ISAD_G')),
            CONSTRAINT ck_registro_descritivo_raiz CHECK (
                (nivel = '1' AND parent_id IS NULL) OR (nivel <> '1' AND parent_id IS NOT NULL)
            ),
            CONSTRAINT ck_registro_descritivo_datas CHECK (
                data_inicial IS NULL OR data_final IS NULL OR data_final >= data_inicial
            )
        );

        CREATE INDEX IF NOT EXISTS ix_registros_descritivos_parent
        ON registros_descritivos(parent_id);

        CREATE INDEX IF NOT EXISTS ix_registros_descritivos_nivel
        ON registros_descritivos(nivel);

        CREATE INDEX IF NOT EXISTS ix_registros_descritivos_busca
        ON registros_descritivos(codigo_referencia, titulo);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS registros_descritivos;")
