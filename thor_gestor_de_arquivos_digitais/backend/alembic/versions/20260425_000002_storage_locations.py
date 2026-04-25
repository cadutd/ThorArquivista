"""add storage location hierarchy

Revision ID: 000002_storage_locations
Revises: 000001_init
Create Date: 2026-04-25
"""

from __future__ import annotations

from alembic import op

revision = "000002_storage_locations"
down_revision = "000001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        r"""
        DO $$ BEGIN
            CREATE TYPE tipo_local_guarda AS ENUM (
                'DEPOSITO',
                'SALA_COFRE',
                'DATA_CENTER',
                'MAPOTECA',
                'LABORATORIO',
                'NUVEM',
                'OUTRO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_zona_guarda AS ENUM (
                'ACERVO_TEXTUAL',
                'CARTOGRAFICO',
                'ICONOGRAFICO',
                'MIDIAS_REMOVIVEIS',
                'FITAS_LTO',
                'STORAGE_ONLINE',
                'QUARENTENA',
                'BACKUP',
                'ACESSO',
                'OUTRO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_estrutura_armazenamento AS ENUM (
                'ESTANTE',
                'ARQUIVO_DESLIZANTE',
                'MAPOTECA',
                'GAVETEIRO',
                'ARMARIO',
                'RACK',
                'COFRE',
                'SERVIDOR',
                'NAS',
                'BUCKET_S3',
                'VOLUME_REDE',
                'UNIDADE_LTO',
                'OUTRO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_compartimento_armazenamento AS ENUM (
                'PRATELEIRA',
                'GAVETA',
                'BANDEJA',
                'SLOT',
                'VOLUME',
                'DIRETORIO',
                'BUCKET',
                'PARTICAO',
                'CAIXA_INTERNA',
                'OUTRO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        DO $$ BEGIN
            CREATE TYPE tipo_posicao_armazenamento AS ENUM (
                'POSICAO_CAIXA',
                'POSICAO_PASTA',
                'POSICAO_VOLUME',
                'POSICAO_MAPA',
                'SLOT_FITA',
                'SLOT_MIDIA',
                'DIRETORIO_AIP',
                'DIRETORIO_SIP',
                'DIRETORIO_DIP',
                'BUCKET_OBJETO',
                'VOLUME_LOGICO',
                'OUTRO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;

        CREATE TABLE IF NOT EXISTS locais_guarda (
            id SERIAL PRIMARY KEY,

            codigo VARCHAR(50) NOT NULL UNIQUE,
            nome VARCHAR(255) NOT NULL,
            tipo_local tipo_local_guarda NOT NULL,

            descricao TEXT,

            logradouro VARCHAR(255),
            numero VARCHAR(50),
            complemento VARCHAR(255),
            bairro VARCHAR(120),
            municipio VARCHAR(120),
            uf CHAR(2),
            cep VARCHAR(20),
            pais VARCHAR(120) DEFAULT 'Brasil',

            observacoes TEXT,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,

            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMPTZ
        );

        CREATE TABLE IF NOT EXISTS zonas_guarda (
            id SERIAL PRIMARY KEY,

            id_local_guarda INTEGER NOT NULL
                REFERENCES locais_guarda(id)
                ON DELETE CASCADE,

            codigo VARCHAR(50) NOT NULL,
            nome VARCHAR(255) NOT NULL,
            tipo_zona tipo_zona_guarda NOT NULL,

            descricao TEXT,

            quantidade_corredores INTEGER,
            quantidade_modulos_por_corredor INTEGER,
            quantidade_estantes_por_modulo INTEGER,
            quantidade_prateleiras_por_estante INTEGER,
            capacidade_caixas_por_prateleira INTEGER,

            observacoes TEXT,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,

            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMPTZ,

            CONSTRAINT uq_zona_por_local UNIQUE (id_local_guarda, codigo),

            CONSTRAINT ck_zona_quantidades_positivas CHECK (
                (quantidade_corredores IS NULL OR quantidade_corredores > 0)
                AND (quantidade_modulos_por_corredor IS NULL OR quantidade_modulos_por_corredor > 0)
                AND (quantidade_estantes_por_modulo IS NULL OR quantidade_estantes_por_modulo > 0)
                AND (quantidade_prateleiras_por_estante IS NULL OR quantidade_prateleiras_por_estante > 0)
                AND (capacidade_caixas_por_prateleira IS NULL OR capacidade_caixas_por_prateleira > 0)
            )
        );

        CREATE TABLE IF NOT EXISTS estruturas_armazenamento (
            id SERIAL PRIMARY KEY,

            id_zona_guarda INTEGER NOT NULL
                REFERENCES zonas_guarda(id)
                ON DELETE CASCADE,

            codigo VARCHAR(50) NOT NULL,
            nome VARCHAR(255) NOT NULL,
            tipo_estrutura tipo_estrutura_armazenamento NOT NULL,

            descricao TEXT,
            ordem INTEGER,
            capacidade_total INTEGER,

            observacoes TEXT,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,

            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMPTZ,

            CONSTRAINT uq_estrutura_por_zona UNIQUE (id_zona_guarda, codigo),

            CONSTRAINT ck_estrutura_ordem_positiva CHECK (
                ordem IS NULL OR ordem > 0
            ),

            CONSTRAINT ck_estrutura_capacidade_positiva CHECK (
                capacidade_total IS NULL OR capacidade_total > 0
            )
        );

        CREATE TABLE IF NOT EXISTS compartimentos_armazenamento (
            id SERIAL PRIMARY KEY,

            id_estrutura_armazenamento INTEGER NOT NULL
                REFERENCES estruturas_armazenamento(id)
                ON DELETE CASCADE,

            codigo VARCHAR(50) NOT NULL,
            nome VARCHAR(255) NOT NULL,
            tipo_compartimento tipo_compartimento_armazenamento NOT NULL,

            descricao TEXT,
            ordem INTEGER,
            capacidade_posicoes INTEGER,

            observacoes TEXT,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,

            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMPTZ,

            CONSTRAINT uq_compartimento_por_estrutura UNIQUE (
                id_estrutura_armazenamento,
                codigo
            ),

            CONSTRAINT ck_compartimento_ordem_positiva CHECK (
                ordem IS NULL OR ordem > 0
            ),

            CONSTRAINT ck_compartimento_capacidade_positiva CHECK (
                capacidade_posicoes IS NULL OR capacidade_posicoes > 0
            )
        );

        CREATE TABLE IF NOT EXISTS posicoes_armazenamento (
            id SERIAL PRIMARY KEY,

            id_compartimento_armazenamento INTEGER NOT NULL
                REFERENCES compartimentos_armazenamento(id)
                ON DELETE CASCADE,

            codigo VARCHAR(50) NOT NULL,
            codigo_completo VARCHAR(500) NOT NULL UNIQUE,

            tipo_posicao tipo_posicao_armazenamento NOT NULL,

            ordem INTEGER,
            capacidade_unidades INTEGER NOT NULL DEFAULT 1,

            ocupada BOOLEAN NOT NULL DEFAULT FALSE,
            ativo BOOLEAN NOT NULL DEFAULT TRUE,

            observacoes TEXT,

            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMPTZ,

            CONSTRAINT uq_posicao_por_compartimento UNIQUE (
                id_compartimento_armazenamento,
                codigo
            ),

            CONSTRAINT ck_posicao_ordem_positiva CHECK (
                ordem IS NULL OR ordem > 0
            ),

            CONSTRAINT ck_posicao_capacidade_positiva CHECK (
                capacidade_unidades > 0
            )
        );

        ALTER TABLE unidades_acondicionamento
        ADD COLUMN IF NOT EXISTS id_posicao_armazenamento INTEGER
            REFERENCES posicoes_armazenamento(id)
            ON DELETE SET NULL;

        ALTER TABLE midias_armazenamento
        ADD COLUMN IF NOT EXISTS id_posicao_armazenamento INTEGER
            REFERENCES posicoes_armazenamento(id)
            ON DELETE SET NULL;

        ALTER TABLE copias_unidades_acondicionamento_digitais
        ADD COLUMN IF NOT EXISTS id_posicao_armazenamento INTEGER
            REFERENCES posicoes_armazenamento(id)
            ON DELETE SET NULL;

        CREATE TABLE IF NOT EXISTS movimentacoes_armazenamento (
            id SERIAL PRIMARY KEY,

            -- Existing domain tables use SERIAL/INTEGER primary keys in 000001_init.
            id_unidade_acondicionamento INTEGER
                REFERENCES unidades_acondicionamento(id)
                ON DELETE CASCADE,

            id_midia_armazenamento INTEGER
                REFERENCES midias_armazenamento(id)
                ON DELETE CASCADE,

            id_copia_unidade_acondicionamento_digital INTEGER
                REFERENCES copias_unidades_acondicionamento_digitais(id)
                ON DELETE CASCADE,

            id_posicao_origem INTEGER
                REFERENCES posicoes_armazenamento(id)
                ON DELETE SET NULL,

            id_posicao_destino INTEGER
                REFERENCES posicoes_armazenamento(id)
                ON DELETE SET NULL,

            data_movimentacao TIMESTAMPTZ NOT NULL DEFAULT now(),

            responsavel VARCHAR(255),
            motivo TEXT,
            observacoes TEXT,

            CONSTRAINT ck_movimentacao_um_objeto CHECK (
                (
                    CASE WHEN id_unidade_acondicionamento IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN id_midia_armazenamento IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN id_copia_unidade_acondicionamento_digital IS NOT NULL THEN 1 ELSE 0 END
                ) = 1
            )
        );

        CREATE INDEX IF NOT EXISTS ix_zonas_local
        ON zonas_guarda(id_local_guarda);

        CREATE INDEX IF NOT EXISTS ix_estruturas_zona
        ON estruturas_armazenamento(id_zona_guarda);

        CREATE INDEX IF NOT EXISTS ix_compartimentos_estrutura
        ON compartimentos_armazenamento(id_estrutura_armazenamento);

        CREATE INDEX IF NOT EXISTS ix_posicoes_compartimento
        ON posicoes_armazenamento(id_compartimento_armazenamento);

        CREATE INDEX IF NOT EXISTS ix_posicoes_codigo_completo
        ON posicoes_armazenamento(codigo_completo);

        CREATE INDEX IF NOT EXISTS ix_posicoes_ocupada
        ON posicoes_armazenamento(ocupada);

        CREATE INDEX IF NOT EXISTS ix_unidades_posicao
        ON unidades_acondicionamento(id_posicao_armazenamento);

        CREATE INDEX IF NOT EXISTS ix_midias_posicao
        ON midias_armazenamento(id_posicao_armazenamento);

        CREATE INDEX IF NOT EXISTS ix_copias_posicao
        ON copias_unidades_acondicionamento_digitais(id_posicao_armazenamento);

        CREATE INDEX IF NOT EXISTS ix_movimentacoes_unidade
        ON movimentacoes_armazenamento(id_unidade_acondicionamento);

        CREATE INDEX IF NOT EXISTS ix_movimentacoes_midia
        ON movimentacoes_armazenamento(id_midia_armazenamento);

        CREATE INDEX IF NOT EXISTS ix_movimentacoes_copia
        ON movimentacoes_armazenamento(id_copia_unidade_acondicionamento_digital);

        CREATE INDEX IF NOT EXISTS ix_movimentacoes_data
        ON movimentacoes_armazenamento(data_movimentacao);
        """
    )


def downgrade() -> None:
    op.execute(
        r"""
        DROP TABLE IF EXISTS movimentacoes_armazenamento;

        DROP INDEX IF EXISTS ix_unidades_posicao;
        DROP INDEX IF EXISTS ix_midias_posicao;
        DROP INDEX IF EXISTS ix_copias_posicao;

        ALTER TABLE copias_unidades_acondicionamento_digitais
        DROP COLUMN IF EXISTS id_posicao_armazenamento;

        ALTER TABLE midias_armazenamento
        DROP COLUMN IF EXISTS id_posicao_armazenamento;

        ALTER TABLE unidades_acondicionamento
        DROP COLUMN IF EXISTS id_posicao_armazenamento;

        DROP TABLE IF EXISTS posicoes_armazenamento;
        DROP TABLE IF EXISTS compartimentos_armazenamento;
        DROP TABLE IF EXISTS estruturas_armazenamento;
        DROP TABLE IF EXISTS zonas_guarda;
        DROP TABLE IF EXISTS locais_guarda;

        DROP TYPE IF EXISTS tipo_posicao_armazenamento;
        DROP TYPE IF EXISTS tipo_compartimento_armazenamento;
        DROP TYPE IF EXISTS tipo_estrutura_armazenamento;
        DROP TYPE IF EXISTS tipo_zona_guarda;
        DROP TYPE IF EXISTS tipo_local_guarda;
        """
    )
