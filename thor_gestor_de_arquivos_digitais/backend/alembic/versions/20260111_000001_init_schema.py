"""init schema (SQL nativo Postgres)

Revision ID: 000001_init
Revises:
Create Date: 2026-01-12
"""

from __future__ import annotations

from alembic import op

revision = "000001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tudo em SQL nativo, executado numa transação do Alembic.
    # Observação: CREATE INDEX CONCURRENTLY não pode ser usado dentro de transação,
    # então usamos CREATE INDEX IF NOT EXISTS (sem concurrently).

    op.execute(
        r"""
        -- =========================
        -- ENUM TYPES (idempotente)
        -- =========================
        DO $$ BEGIN
            CREATE TYPE tipo_suporte AS ENUM ('fisico','digital','hibrido');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_unidade AS ENUM ('caixa','pasta','volume','aip','sip','dip');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE nivel_acesso AS ENUM ('publico','restrito','confidencial');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE status_unidade AS ENUM ('ativa','inativa','transferida','eliminada');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_midia_armazenamento AS ENUM ('filesystem','nas','nfs','lto','s3','cloud');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE funcao_copia AS ENUM ('preservacao','backup','acesso','quarentena');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE status_copia AS ENUM ('ativa','indisponivel','corrompida','em_verificacao');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_evento_preservacao AS ENUM
                ('ingestao','validacao','fixidez','replicacao','migracao','acesso','movimentacao','outro');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE resultado_evento_preservacao AS ENUM ('sucesso','falha','alerta','indeterminado');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        -- =========================
        -- TABELAS
        -- =========================

        -- Unidades de acondicionamento (base)
        CREATE TABLE IF NOT EXISTS unidades_acondicionamento (
            id                 SERIAL PRIMARY KEY,
            identificador      VARCHAR(255) NOT NULL,
            titulo             VARCHAR(500) NOT NULL,
            descricao          VARCHAR(2000),
            tipo_suporte       tipo_suporte NOT NULL,
            tipo_unidade       tipo_unidade NOT NULL,
            nivel_acesso       nivel_acesso NOT NULL DEFAULT 'restrito',
            status             status_unidade NOT NULL DEFAULT 'ativa',
            id_unidade_pai     INTEGER NULL,
            id_representa      INTEGER NULL,
            criado_em          TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em      TIMESTAMPTZ NULL,
            CONSTRAINT uq_unidade_acondicionamento_identificador UNIQUE (identificador),
            CONSTRAINT fk_unidade_pai FOREIGN KEY (id_unidade_pai) REFERENCES unidades_acondicionamento(id),
            CONSTRAINT fk_unidade_representa FOREIGN KEY (id_representa) REFERENCES unidades_acondicionamento(id)
        );

        -- Extensão digital (1:1 com unidade)
        CREATE TABLE IF NOT EXISTS unidades_acondicionamento_digitais (
            id_unidade_acondicionamento INTEGER PRIMARY KEY
                REFERENCES unidades_acondicionamento(id),
            tamanho_bytes               BIGINT,
            status_fixidez              VARCHAR(50)
        );

        -- Mídias de armazenamento
        CREATE TABLE IF NOT EXISTS midias_armazenamento (
            id        SERIAL PRIMARY KEY,
            nome      VARCHAR(255) NOT NULL,
            tipo      tipo_midia_armazenamento NOT NULL,
            descricao VARCHAR(2000),
            ativo     BOOLEAN NOT NULL DEFAULT true,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_midia_armazenamento_nome UNIQUE (nome)
        );

        -- Cópias da unidade digital em mídias
        CREATE TABLE IF NOT EXISTS copias_unidades_acondicionamento_digitais (
            id                      SERIAL PRIMARY KEY,
            id_unidade_acondicionamento INTEGER NOT NULL
                REFERENCES unidades_acondicionamento(id),
            id_midia_armazenamento  INTEGER NOT NULL
                REFERENCES midias_armazenamento(id),
            uri_copia               VARCHAR(1200) NOT NULL,
            funcao_copia            funcao_copia NOT NULL,
            status_copia            status_copia NOT NULL DEFAULT 'ativa',
            algoritmo_fixidez       VARCHAR(32),
            hash_fixidez            VARCHAR(128),
            ultima_verificacao_em   TIMESTAMPTZ,
            criada_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_copia_unidade_acondicionamento_midia_uri
                UNIQUE (id_unidade_acondicionamento, id_midia_armazenamento, uri_copia)
        );

        -- Eventos de preservação
        CREATE TABLE IF NOT EXISTS eventos_preservacao (
            id                      SERIAL PRIMARY KEY,
            id_unidade_acondicionamento INTEGER NOT NULL
                REFERENCES unidades_acondicionamento(id),
            tipo_evento             tipo_evento_preservacao NOT NULL,
            resultado               resultado_evento_preservacao NOT NULL DEFAULT 'sucesso',
            detalhe                 TEXT,
            agente                  VARCHAR(255),
            correlacao              VARCHAR(255),
            criado_em               TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        -- =========================
        -- ÍNDICES (idempotente)
        -- =========================

        -- unidades_acondicionamento
        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_identificador
            ON unidades_acondicionamento (identificador);
        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_tipo_suporte
            ON unidades_acondicionamento (tipo_suporte);
        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_tipo_unidade
            ON unidades_acondicionamento (tipo_unidade);
        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_nivel_acesso
            ON unidades_acondicionamento (nivel_acesso);
        CREATE INDEX IF NOT EXISTS ix_unidades_acondicionamento_status
            ON unidades_acondicionamento (status);

        -- midias_armazenamento
        CREATE INDEX IF NOT EXISTS ix_midias_armazenamento_nome
            ON midias_armazenamento (nome);
        CREATE INDEX IF NOT EXISTS ix_midias_armazenamento_tipo
            ON midias_armazenamento (tipo);
        CREATE INDEX IF NOT EXISTS ix_midias_armazenamento_ativo
            ON midias_armazenamento (ativo);

        -- copias_unidades_acondicionamento_digitais
        CREATE INDEX IF NOT EXISTS ix_copia_unidade_acondicionamento_funcao
            ON copias_unidades_acondicionamento_digitais (id_unidade_acondicionamento, funcao_copia);

        -- eventos_preservacao
        CREATE INDEX IF NOT EXISTS ix_eventos_preservacao_unidade
            ON eventos_preservacao (id_unidade_acondicionamento);
        CREATE INDEX IF NOT EXISTS ix_eventos_preservacao_tipo
            ON eventos_preservacao (tipo_evento);
        CREATE INDEX IF NOT EXISTS ix_eventos_preservacao_resultado
            ON eventos_preservacao (resultado);
        CREATE INDEX IF NOT EXISTS ix_eventos_preservacao_correlacao
            ON eventos_preservacao (correlacao);
        CREATE INDEX IF NOT EXISTS ix_eventos_preservacao_criado_em
            ON eventos_preservacao (criado_em);
        """
    )


def downgrade() -> None:
    # Em downgrade “manual”, removemos tabelas e tipos na ordem correta.
    # IF EXISTS deixa tolerante.
    op.execute(
        r"""
        DROP TABLE IF EXISTS eventos_preservacao;
        DROP TABLE IF EXISTS copias_unidades_acondicionamento_digitais;
        DROP TABLE IF EXISTS midias_armazenamento;
        DROP TABLE IF EXISTS unidades_acondicionamento_digitais;
        DROP TABLE IF EXISTS unidades_acondicionamento;

        DROP TYPE IF EXISTS resultado_evento_preservacao;
        DROP TYPE IF EXISTS tipo_evento_preservacao;
        DROP TYPE IF EXISTS status_copia;
        DROP TYPE IF EXISTS funcao_copia;
        DROP TYPE IF EXISTS tipo_midia_armazenamento;
        DROP TYPE IF EXISTS status_unidade;
        DROP TYPE IF EXISTS nivel_acesso;
        DROP TYPE IF EXISTS tipo_unidade;
        DROP TYPE IF EXISTS tipo_suporte;
        """
    )
