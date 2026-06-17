"""permissoes do ciclo de vida de midias

Revision ID: 20260616_000031
Revises: 20260616_000030
Create Date: 2026-06-16
"""

from __future__ import annotations

from alembic import op


revision = "20260616_000031"
down_revision = "20260616_000030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        WITH permissoes_base (codigo, nome, descricao, modulo, funcao, acao) AS (
            VALUES
                ('midias.criar', 'Criar Mídias de armazenamento', 'Permite cadastrar mídias de armazenamento.', 'preservacao-digital', 'midias', 'CRIAR'),
                ('midias.editar', 'Editar Mídias de armazenamento', 'Permite editar, ativar e desativar mídias de armazenamento.', 'preservacao-digital', 'midias', 'EDITAR'),
                ('midias.consultar', 'Consultar Mídias de armazenamento', 'Permite consultar a listagem, detalhes e metadados das mídias de armazenamento.', 'preservacao-digital', 'midias', 'CONSULTAR'),
                ('midias.excluir', 'Excluir Mídias de armazenamento', 'Permite excluir ou desativar registros de mídias conforme regra de negócio.', 'preservacao-digital', 'midias', 'EXCLUIR'),

                ('tipos-midia.criar', 'Criar Tipos de mídia', 'Permite cadastrar tipos de mídia e seus parâmetros de ciclo de vida.', 'administracao', 'tipos-midia', 'CRIAR'),
                ('tipos-midia.editar', 'Editar Tipos de mídia', 'Permite editar, ativar e desativar tipos de mídia.', 'administracao', 'tipos-midia', 'EDITAR'),
                ('tipos-midia.consultar', 'Consultar Tipos de mídia', 'Permite consultar tipos de mídia cadastrados.', 'administracao', 'tipos-midia', 'CONSULTAR'),
                ('tipos-midia.excluir', 'Excluir Tipos de mídia', 'Permite excluir ou desativar tipos de mídia conforme vínculo histórico.', 'administracao', 'tipos-midia', 'EXCLUIR'),

                ('migracoes-midias.criar', 'Criar Migrações de mídias', 'Permite iniciar migrações de mídia de armazenamento.', 'preservacao-digital', 'migracoes-midias', 'CRIAR'),
                ('migracoes-midias.editar', 'Editar Migrações de mídias', 'Permite atualizar etapas, relatórios e conclusão de migrações.', 'preservacao-digital', 'migracoes-midias', 'EDITAR'),
                ('migracoes-midias.consultar', 'Consultar Migrações de mídias', 'Permite consultar migrações de mídias e seus relatórios.', 'preservacao-digital', 'migracoes-midias', 'CONSULTAR'),
                ('migracoes-midias.excluir', 'Excluir Migrações de mídias', 'Permite cancelar ou remover registros de migração quando a regra permitir.', 'preservacao-digital', 'migracoes-midias', 'EXCLUIR'),

                ('integridade-midias.criar', 'Criar Verificações de integridade de mídias', 'Permite registrar verificações manuais ou importar relatórios de integridade.', 'preservacao-digital', 'integridade-midias', 'CRIAR'),
                ('integridade-midias.editar', 'Editar Verificações de integridade de mídias', 'Permite atualizar rotinas e registros de verificação quando a regra permitir.', 'preservacao-digital', 'integridade-midias', 'EDITAR'),
                ('integridade-midias.consultar', 'Consultar Painel de integridade de mídias', 'Permite acessar o painel de integridade e consultar verificações de mídias.', 'preservacao-digital', 'integridade-midias', 'CONSULTAR'),
                ('integridade-midias.excluir', 'Excluir Verificações de integridade de mídias', 'Permite remover registros de verificação quando a regra permitir.', 'preservacao-digital', 'integridade-midias', 'EXCLUIR'),

                ('eventos-midia.criar', 'Criar Eventos de mídias de armazenamento', 'Permite registrar eventos PREMIS diretamente sobre mídias de armazenamento.', 'preservacao-digital', 'eventos-midia', 'CRIAR'),
                ('eventos-midia.editar', 'Editar Eventos de mídias de armazenamento', 'Permite ajustar eventos de mídias quando a regra permitir.', 'preservacao-digital', 'eventos-midia', 'EDITAR'),
                ('eventos-midia.consultar', 'Consultar Eventos de mídias de armazenamento', 'Permite consultar o histórico PREMIS de mídias de armazenamento.', 'preservacao-digital', 'eventos-midia', 'CONSULTAR'),
                ('eventos-midia.excluir', 'Excluir Eventos de mídias de armazenamento', 'Permite remover eventos de mídias quando a regra permitir.', 'preservacao-digital', 'eventos-midia', 'EXCLUIR')
        )
        INSERT INTO permissoes (id, codigo, nome, descricao, modulo, funcao, acao, ativo)
        SELECT gen_random_uuid(), codigo, nome, descricao, modulo, funcao, acao, TRUE
          FROM permissoes_base
        ON CONFLICT (codigo) DO UPDATE SET
            nome = EXCLUDED.nome,
            descricao = EXCLUDED.descricao,
            modulo = EXCLUDED.modulo,
            funcao = EXCLUDED.funcao,
            acao = EXCLUDED.acao,
            ativo = TRUE,
            atualizado_em = now();

        DELETE FROM perfil_permissao pp
         USING perfis pf, permissoes pe
         WHERE pp.perfil_id = pf.id
           AND pp.permissao_id = pe.id
           AND pf.codigo IN ('ADMIN', 'ARQUIVISTA', 'ADMISSAO', 'GESTOR_ARMAZENAMENTO', 'CONSULTA')
           AND pe.funcao IN ('midias', 'tipos-midia', 'migracoes-midias', 'integridade-midias', 'eventos-midia');

        WITH matriz (perfil_codigo, funcao, acao) AS (
            VALUES
                ('ADMIN', 'midias', 'CRIAR'), ('ADMIN', 'midias', 'EDITAR'), ('ADMIN', 'midias', 'CONSULTAR'), ('ADMIN', 'midias', 'EXCLUIR'),
                ('ADMIN', 'tipos-midia', 'CRIAR'), ('ADMIN', 'tipos-midia', 'EDITAR'), ('ADMIN', 'tipos-midia', 'CONSULTAR'), ('ADMIN', 'tipos-midia', 'EXCLUIR'),
                ('ADMIN', 'migracoes-midias', 'CRIAR'), ('ADMIN', 'migracoes-midias', 'EDITAR'), ('ADMIN', 'migracoes-midias', 'CONSULTAR'), ('ADMIN', 'migracoes-midias', 'EXCLUIR'),
                ('ADMIN', 'integridade-midias', 'CRIAR'), ('ADMIN', 'integridade-midias', 'EDITAR'), ('ADMIN', 'integridade-midias', 'CONSULTAR'), ('ADMIN', 'integridade-midias', 'EXCLUIR'),
                ('ADMIN', 'eventos-midia', 'CRIAR'), ('ADMIN', 'eventos-midia', 'EDITAR'), ('ADMIN', 'eventos-midia', 'CONSULTAR'), ('ADMIN', 'eventos-midia', 'EXCLUIR'),

                ('GESTOR_ARMAZENAMENTO', 'midias', 'CRIAR'), ('GESTOR_ARMAZENAMENTO', 'midias', 'EDITAR'), ('GESTOR_ARMAZENAMENTO', 'midias', 'CONSULTAR'), ('GESTOR_ARMAZENAMENTO', 'midias', 'EXCLUIR'),
                ('GESTOR_ARMAZENAMENTO', 'tipos-midia', 'CRIAR'), ('GESTOR_ARMAZENAMENTO', 'tipos-midia', 'EDITAR'), ('GESTOR_ARMAZENAMENTO', 'tipos-midia', 'CONSULTAR'), ('GESTOR_ARMAZENAMENTO', 'tipos-midia', 'EXCLUIR'),
                ('GESTOR_ARMAZENAMENTO', 'migracoes-midias', 'CRIAR'), ('GESTOR_ARMAZENAMENTO', 'migracoes-midias', 'EDITAR'), ('GESTOR_ARMAZENAMENTO', 'migracoes-midias', 'CONSULTAR'), ('GESTOR_ARMAZENAMENTO', 'migracoes-midias', 'EXCLUIR'),
                ('GESTOR_ARMAZENAMENTO', 'integridade-midias', 'CRIAR'), ('GESTOR_ARMAZENAMENTO', 'integridade-midias', 'EDITAR'), ('GESTOR_ARMAZENAMENTO', 'integridade-midias', 'CONSULTAR'), ('GESTOR_ARMAZENAMENTO', 'integridade-midias', 'EXCLUIR'),
                ('GESTOR_ARMAZENAMENTO', 'eventos-midia', 'CRIAR'), ('GESTOR_ARMAZENAMENTO', 'eventos-midia', 'EDITAR'), ('GESTOR_ARMAZENAMENTO', 'eventos-midia', 'CONSULTAR'), ('GESTOR_ARMAZENAMENTO', 'eventos-midia', 'EXCLUIR'),

                ('ARQUIVISTA', 'midias', 'CONSULTAR'),
                ('ARQUIVISTA', 'tipos-midia', 'CONSULTAR'),
                ('ARQUIVISTA', 'migracoes-midias', 'CONSULTAR'),
                ('ARQUIVISTA', 'integridade-midias', 'CONSULTAR'),
                ('ARQUIVISTA', 'eventos-midia', 'CONSULTAR'),

                ('ADMISSAO', 'midias', 'CONSULTAR'),
                ('ADMISSAO', 'tipos-midia', 'CONSULTAR'),

                ('CONSULTA', 'midias', 'CONSULTAR'),
                ('CONSULTA', 'migracoes-midias', 'CONSULTAR'),
                ('CONSULTA', 'integridade-midias', 'CONSULTAR'),
                ('CONSULTA', 'eventos-midia', 'CONSULTAR')
        )
        INSERT INTO perfil_permissao (perfil_id, permissao_id)
        SELECT pf.id, pe.id
          FROM matriz m
          JOIN perfis pf ON pf.codigo = m.perfil_codigo
          JOIN permissoes pe ON pe.funcao = m.funcao AND pe.acao = m.acao
        ON CONFLICT DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM perfil_permissao pp
         USING perfis pf, permissoes pe
         WHERE pp.perfil_id = pf.id
           AND pp.permissao_id = pe.id
           AND pf.codigo IN ('ADMIN', 'ARQUIVISTA', 'ADMISSAO', 'GESTOR_ARMAZENAMENTO', 'CONSULTA')
           AND pe.funcao IN ('tipos-midia', 'migracoes-midias', 'integridade-midias', 'eventos-midia');

        DELETE FROM permissoes
         WHERE funcao IN ('tipos-midia', 'migracoes-midias', 'integridade-midias', 'eventos-midia');
        """
    )
