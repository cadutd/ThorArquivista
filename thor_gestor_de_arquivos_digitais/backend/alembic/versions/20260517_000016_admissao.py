"""create admission module tables

Revision ID: 20260517_000016
Revises: 20260517_000015
Create Date: 2026-05-17
"""

from __future__ import annotations

from alembic import op

revision = "20260517_000016"
down_revision = "20260517_000015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS processos_admissao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            numero_processo VARCHAR(100) NOT NULL UNIQUE,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT,
            id_instituicao_arquivo UUID NOT NULL REFERENCES instituicao_arquivo(id),
            id_entidade_produtora UUID NOT NULL REFERENCES entidades_produtoras(id),
            tipo_processo_admissao VARCHAR(50) NOT NULL,
            tipo_ingresso VARCHAR(50) NOT NULL,
            tipo_suporte VARCHAR(50) NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim_prevista DATE,
            data_encerramento DATE,
            processo_ativo BOOLEAN NOT NULL DEFAULT TRUE,
            admissoes_recorrentes BOOLEAN NOT NULL DEFAULT FALSE,
            status VARCHAR(50) NOT NULL DEFAULT 'ABERTO',
            resultado_final VARCHAR(50),
            id_descricao_arquivistica UUID REFERENCES registros_descritivos(id),
            codigo_classificacao VARCHAR(100),
            codigo_classificacao_descricao VARCHAR(255),
            restricao_acesso VARCHAR(255),
            hipotese_legal_restricao VARCHAR(255),
            volume_estimado VARCHAR(100),
            volume_recebido VARCHAR(100),
            quantidade_unidades_estimadas INTEGER,
            quantidade_unidades_recebidas INTEGER,
            observacoes TEXT,
            parecer_final TEXT,
            criado_por VARCHAR(255),
            atualizado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS ix_processos_admissao_numero ON processos_admissao(numero_processo);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_titulo ON processos_admissao(titulo);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_instituicao ON processos_admissao(id_instituicao_arquivo);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_entidade ON processos_admissao(id_entidade_produtora);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_tipo_processo ON processos_admissao(tipo_processo_admissao);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_tipo_ingresso ON processos_admissao(tipo_ingresso);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_tipo_suporte ON processos_admissao(tipo_suporte);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_status ON processos_admissao(status);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_ativo ON processos_admissao(processo_ativo);
        CREATE INDEX IF NOT EXISTS ix_processos_admissao_data_inicio ON processos_admissao(data_inicio);

        CREATE TABLE IF NOT EXISTS reunioes_admissao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_processo_admissao UUID NOT NULL REFERENCES processos_admissao(id) ON DELETE CASCADE,
            numero_reuniao INTEGER NOT NULL,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT,
            tipo_reuniao VARCHAR(50) NOT NULL,
            data_reuniao TIMESTAMP WITH TIME ZONE NOT NULL,
            participantes TEXT,
            deliberacoes TEXT,
            pendencias TEXT,
            proximos_passos TEXT,
            criado_por VARCHAR(255),
            atualizado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_reuniao_admissao_numero UNIQUE (id_processo_admissao, numero_reuniao)
        );
        CREATE INDEX IF NOT EXISTS ix_reunioes_admissao_processo ON reunioes_admissao(id_processo_admissao);
        CREATE INDEX IF NOT EXISTS ix_reunioes_admissao_tipo ON reunioes_admissao(tipo_reuniao);

        CREATE TABLE IF NOT EXISTS acordos_admissao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_processo_admissao UUID NOT NULL REFERENCES processos_admissao(id) ON DELETE CASCADE,
            numero_versao INTEGER NOT NULL,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'RASCUNHO',
            data_inicio_vigencia DATE,
            data_fim_vigencia DATE,
            motivo_revisao TEXT,
            regras_empacotamento TEXT,
            regras_nomenclatura TEXT,
            formatos_aceitos TEXT,
            metadados_obrigatorios TEXT,
            requisitos_fixidez TEXT,
            requisitos_representacao TEXT,
            politica_validacao TEXT,
            politica_rejeicao TEXT,
            politica_normalizacao TEXT,
            politica_sigilo TEXT,
            periodicidade_submissao VARCHAR(100),
            observacoes TEXT,
            documento_acordo VARCHAR(500),
            criado_por VARCHAR(255),
            atualizado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_acordo_admissao_versao UNIQUE (id_processo_admissao, numero_versao)
        );
        CREATE INDEX IF NOT EXISTS ix_acordos_admissao_processo ON acordos_admissao(id_processo_admissao);
        CREATE INDEX IF NOT EXISTS ix_acordos_admissao_status ON acordos_admissao(status);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_acordo_admissao_ativo_por_processo
            ON acordos_admissao(id_processo_admissao)
            WHERE status = 'ATIVO';

        CREATE TABLE IF NOT EXISTS sessoes_submissao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_processo_admissao UUID NOT NULL REFERENCES processos_admissao(id) ON DELETE CASCADE,
            id_acordo_utilizado UUID NOT NULL REFERENCES acordos_admissao(id),
            numero_sessao INTEGER NOT NULL,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT,
            data_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
            data_fim TIMESTAMP WITH TIME ZONE,
            canal_submissao VARCHAR(50) NOT NULL,
            protocolo_transferencia VARCHAR(255),
            responsavel_envio VARCHAR(255),
            responsavel_recebimento VARCHAR(255),
            tipo_suporte VARCHAR(50) NOT NULL,
            volume_informado VARCHAR(100),
            volume_recebido VARCHAR(100),
            quantidade_itens_informada INTEGER,
            quantidade_itens_recebida INTEGER,
            caminho_origem VARCHAR(500),
            caminho_destino_quarentena VARCHAR(500),
            status VARCHAR(50) NOT NULL DEFAULT 'INICIADA',
            resultado_validacao TEXT,
            observacoes TEXT,
            criado_por VARCHAR(255),
            atualizado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            CONSTRAINT uq_sessao_submissao_numero UNIQUE (id_processo_admissao, numero_sessao)
        );
        CREATE INDEX IF NOT EXISTS ix_sessoes_submissao_processo ON sessoes_submissao(id_processo_admissao);
        CREATE INDEX IF NOT EXISTS ix_sessoes_submissao_acordo ON sessoes_submissao(id_acordo_utilizado);
        CREATE INDEX IF NOT EXISTS ix_sessoes_submissao_status ON sessoes_submissao(status);

        CREATE TABLE IF NOT EXISTS sips_admissao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_processo_admissao UUID NOT NULL REFERENCES processos_admissao(id) ON DELETE CASCADE,
            id_sessao_submissao UUID NOT NULL REFERENCES sessoes_submissao(id) ON DELETE CASCADE,
            codigo_sip VARCHAR(100) NOT NULL UNIQUE,
            titulo VARCHAR(255) NOT NULL,
            descricao TEXT,
            tipo_sip VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'RECEBIDO',
            data_recebimento TIMESTAMP WITH TIME ZONE NOT NULL,
            estrutura_original TEXT,
            caminho_armazenamento_temporario VARCHAR(500),
            manifesto_arquivos TEXT,
            algoritmo_hash VARCHAR(50),
            hash_global VARCHAR(255),
            tamanho_bytes BIGINT,
            quantidade_arquivos INTEGER,
            quantidade_unidades_fisicas INTEGER,
            resultado_validacao TEXT,
            observacoes TEXT,
            criado_por VARCHAR(255),
            atualizado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_sips_admissao_processo ON sips_admissao(id_processo_admissao);
        CREATE INDEX IF NOT EXISTS ix_sips_admissao_sessao ON sips_admissao(id_sessao_submissao);
        CREATE INDEX IF NOT EXISTS ix_sips_admissao_codigo ON sips_admissao(codigo_sip);
        CREATE INDEX IF NOT EXISTS ix_sips_admissao_status ON sips_admissao(status);

        CREATE TABLE IF NOT EXISTS relacoes_sip_aip (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_sip UUID NOT NULL REFERENCES sips_admissao(id) ON DELETE CASCADE,
            id_unidade_acondicionamento INTEGER NOT NULL REFERENCES unidades_acondicionamento(id),
            tipo_relacao VARCHAR(50) NOT NULL DEFAULT 'ORIGEM_TOTAL',
            observacoes TEXT,
            criado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_relacoes_sip_aip_sip ON relacoes_sip_aip(id_sip);
        CREATE INDEX IF NOT EXISTS ix_relacoes_sip_aip_unidade ON relacoes_sip_aip(id_unidade_acondicionamento);

        CREATE TABLE IF NOT EXISTS eventos_admissao (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            id_processo_admissao UUID NOT NULL REFERENCES processos_admissao(id) ON DELETE CASCADE,
            id_sessao_submissao UUID REFERENCES sessoes_submissao(id) ON DELETE SET NULL,
            id_sip UUID REFERENCES sips_admissao(id) ON DELETE SET NULL,
            id_unidade_acondicionamento INTEGER REFERENCES unidades_acondicionamento(id) ON DELETE SET NULL,
            tipo_evento VARCHAR(50) NOT NULL,
            descricao TEXT NOT NULL,
            resultado VARCHAR(50) NOT NULL DEFAULT 'INFORMATIVO',
            agente VARCHAR(255),
            data_evento TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            detalhe_tecnico TEXT,
            evidencia VARCHAR(500),
            criado_por VARCHAR(255),
            criado_em TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS ix_eventos_admissao_processo ON eventos_admissao(id_processo_admissao);
        CREATE INDEX IF NOT EXISTS ix_eventos_admissao_sessao ON eventos_admissao(id_sessao_submissao);
        CREATE INDEX IF NOT EXISTS ix_eventos_admissao_sip ON eventos_admissao(id_sip);
        CREATE INDEX IF NOT EXISTS ix_eventos_admissao_unidade ON eventos_admissao(id_unidade_acondicionamento);
        CREATE INDEX IF NOT EXISTS ix_eventos_admissao_tipo ON eventos_admissao(tipo_evento);
        CREATE INDEX IF NOT EXISTS ix_eventos_admissao_data ON eventos_admissao(data_evento);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS eventos_admissao;
        DROP TABLE IF EXISTS relacoes_sip_aip;
        DROP TABLE IF EXISTS sips_admissao;
        DROP TABLE IF EXISTS sessoes_submissao;
        DROP INDEX IF EXISTS uq_acordo_admissao_ativo_por_processo;
        DROP TABLE IF EXISTS acordos_admissao;
        DROP TABLE IF EXISTS reunioes_admissao;
        DROP TABLE IF EXISTS processos_admissao;
        """
    )
