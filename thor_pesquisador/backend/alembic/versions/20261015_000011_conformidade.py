"""Phase 5: additive audit, durable jobs, holds and least-privilege defaults."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261015_000011"
down_revision = "20261014_000010"
branch_labels = None
depends_on = None

ADDITIONS = {
    "GESTOR_INSTRUMENTOS": ["auditoria_consultar", "relatorios_consultar", "exportacoes_consultar",
                           "exportacoes_incluir", "exportacoes_excluir", "exportacoes_repetir"],
    "REVISOR": ["auditoria_consultar", "relatorios_consultar"],
}


def upgrade():
    for statement in DDL:
        op.execute(statement)
    op.add_column("instrumentos", sa.Column("revisao_dados", sa.Integer(), nullable=False, server_default="0"))
    for name in ("retencao_bloqueada",):
        op.add_column("editorial_registros", sa.Column(name, sa.Boolean(), nullable=False, server_default="false"))
    for name in ("reter_ate", "expurgo_iniciado_em", "expurgado_em"):
        op.add_column("editorial_registros", sa.Column(name, sa.DateTime(timezone=True)))
    for table in ("eventos_editoriais", "auditoria_imagens"):
        op.add_column(table, sa.Column("request_id", sa.String(64)))
        op.create_index("ix_" + table + "_request_id", table, ["request_id"])
    op.add_column("auditoria_imagens", sa.Column("agente", sa.String(255)))
    # Store exact pre/post values: downgrade must not undo later customizations.
    op.create_table("fase5_perfis_migrados", sa.Column("nome", sa.String(40), primary_key=True),
                    sa.Column("antes", JSONB, nullable=False), sa.Column("depois", JSONB, nullable=False))
    conn = op.get_bind()
    table = sa.table("papeis", sa.column("nome"), sa.column("permissoes", JSONB))
    saved = sa.table("fase5_perfis_migrados", sa.column("nome"), sa.column("antes", JSONB), sa.column("depois", JSONB))
    for nome, additions in ADDITIONS.items():
        old = conn.scalar(sa.select(table.c.permissoes).where(table.c.nome == nome))
        if old is not None and set(old) == set(BASELINE_PERMISSIONS[nome]):
            new = sorted(set(old) | set(additions))
            conn.execute(saved.insert().values(nome=nome, antes=old, depois=new))
            conn.execute(table.update().where(table.c.nome == nome).values(permissoes=new))
    # Append-only evidence is never a retention target, even for expired sessions.
    for table_name in ("auditoria_geral", "eventos_editoriais", "auditoria_imagens"):
        op.execute(f"""CREATE FUNCTION impedir_mutacao_{table_name}() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN RAISE EXCEPTION 'Historico imutavel'; END $$""")
        op.execute(f"""CREATE TRIGGER historico_imutavel BEFORE UPDATE OR DELETE ON {table_name}
          FOR EACH ROW EXECUTE FUNCTION impedir_mutacao_{table_name}()""")


def downgrade():
    conn = op.get_bind()
    if conn.scalar(sa.text("SELECT EXISTS(SELECT 1 FROM auditoria_geral UNION ALL SELECT 1 FROM exportacoes UNION ALL SELECT 1 FROM execucoes_retencao)")):
        raise RuntimeError("Historico da fase 5 existente; exporte e planeje rollback sem apagar evidencias.")
    conn.execute(sa.text("""UPDATE papeis p SET permissoes = m.antes FROM fase5_perfis_migrados m
        WHERE p.nome=m.nome AND p.permissoes=m.depois"""))
    for table in ("auditoria_geral", "eventos_editoriais", "auditoria_imagens"):
        op.execute(f"DROP TRIGGER historico_imutavel ON {table}")
        op.execute(f"DROP FUNCTION impedir_mutacao_{table}()")
    for table in ("eventos_editoriais", "auditoria_imagens"):
        op.drop_index("ix_" + table + "_request_id", table_name=table)
        op.drop_column(table, "request_id")
    op.drop_column("auditoria_imagens", "agente")
    for name in ("retencao_bloqueada", "reter_ate", "expurgo_iniciado_em", "expurgado_em"):
        op.drop_column("editorial_registros", name)
    op.drop_column("instrumentos", "revisao_dados")
    for table in ("fase5_perfis_migrados", "logs_requisicoes", "execucoes_retencao", "politicas_retencao",
                  "exportacao_partes", "exportacoes", "auditoria_geral"):
        op.drop_table(table)

BASELINE_PERMISSIONS = {
    "GESTOR_INSTRUMENTOS": [
        "arquivar",
        "campos_consultar",
        "campos_editar",
        "campos_excluir",
        "campos_incluir",
        "dashboard_consultar",
        "editorial_consultar",
        "enviar_revisao",
        "galerias_consultar",
        "galerias_editar",
        "galerias_excluir",
        "galerias_incluir",
        "imagens_consultar",
        "imagens_editar",
        "imagens_excluir",
        "imagens_incluir",
        "instrumentos_consultar",
        "instrumentos_editar",
        "instrumentos_excluir",
        "instrumentos_incluir",
        "pesquisa_consultar",
        "publicar",
        "registros_consultar",
        "registros_editar",
        "registros_excluir",
        "registros_incluir",
        "reindexar"
    ],
    "REVISOR": [
        "campos_consultar",
        "dashboard_consultar",
        "editorial_consultar",
        "galerias_consultar",
        "imagens_consultar",
        "instrumentos_consultar",
        "pesquisa_consultar",
        "registros_consultar",
        "revisar"
    ]
}

DDL = [
    "\nCREATE TABLE auditoria_geral (\n\tid UUID NOT NULL, \n\tusuario_id UUID, \n\tagente VARCHAR(255) NOT NULL, \n\tacao VARCHAR(60) NOT NULL, \n\tentidade VARCHAR(60) NOT NULL, \n\tentidade_id VARCHAR(255), \n\tinstrumento_id UUID, \n\tregistro_id VARCHAR(255), \n\trequest_id VARCHAR(64), \n\toperacao_id UUID, \n\tdetalhe JSONB NOT NULL, \n\tcriado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id)\n)\n\n",
    "\nCREATE TABLE exportacoes (\n\tid UUID NOT NULL, \n\tusuario_id UUID NOT NULL, \n\tagente VARCHAR(255) NOT NULL, \n\tinstrumento_id UUID NOT NULL, \n\toperacao_id UUID NOT NULL, \n\tformato VARCHAR(20) NOT NULL, \n\tescopo VARCHAR(20) NOT NULL, \n\tstatus VARCHAR(20) DEFAULT 'PENDENTE' NOT NULL, \n\trevisao INTEGER NOT NULL, \n\tschema_json JSONB NOT NULL, \n\tparametros JSONB NOT NULL, \n\tcheckpoint VARCHAR(255), \n\tprocessados INTEGER DEFAULT '0' NOT NULL, \n\tpartes INTEGER DEFAULT '0' NOT NULL, \n\ttentativa INTEGER DEFAULT '1' NOT NULL, \n\tlease_token UUID, \n\tlease_ate TIMESTAMP WITH TIME ZONE, \n\tobject_key TEXT, \n\tchecksum VARCHAR(64), \n\ttamanho_bytes BIGINT, \n\terro VARCHAR(255), \n\texpira_em TIMESTAMP WITH TIME ZONE NOT NULL, \n\tcriado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tatualizado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCONSTRAINT uq_exportacao_operacao UNIQUE (usuario_id, operacao_id), \n\tCHECK (status IN ('PENDENTE','PROCESSANDO','CONCLUIDA','FALHOU','CANCELADA','EXPIRADA','DESCARTADA')), \n\tCHECK (formato IN ('CSV','JSON','PACOTE')), \n\tCHECK (escopo IN ('ADMINISTRATIVO','PUBLICADO'))\n)\n\n",
    "\nCREATE TABLE exportacao_partes (\n\tjob_id UUID NOT NULL, \n\tnumero INTEGER NOT NULL, \n\tobject_key TEXT NOT NULL, \n\tchecksum VARCHAR(64) NOT NULL, \n\tquantidade INTEGER NOT NULL, \n\tPRIMARY KEY (job_id, numero)\n)\n\n",
    "\nCREATE TABLE politicas_retencao (\n\tid UUID NOT NULL, \n\tnome VARCHAR(150) NOT NULL, \n\tcategoria VARCHAR(30) NOT NULL, \n\tdias INTEGER NOT NULL, \n\tinstrumento_id UUID, \n\tativo BOOLEAN DEFAULT 'true' NOT NULL, \n\tpermitir_expurgo BOOLEAN DEFAULT 'false' NOT NULL, \n\tbloqueada BOOLEAN DEFAULT 'false' NOT NULL, \n\tcriado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tatualizado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (dias >= 1 AND dias <= 36500), \n\tCHECK (categoria IN ('LOG_TECNICO','ACESSO_CONSULTIVO','EXPORTACAO','SESSAO','REGISTRO_EXCLUIDO')), \n\tUNIQUE (nome)\n)\n\n",
    "\nCREATE TABLE execucoes_retencao (\n\tid UUID NOT NULL, \n\tpolitica_id UUID NOT NULL, \n\tusuario_id UUID NOT NULL, \n\tagente VARCHAR(255) NOT NULL, \n\toperacao_id UUID NOT NULL, \n\tsimulacao BOOLEAN NOT NULL, \n\tstatus VARCHAR(20) NOT NULL, \n\tcheckpoint VARCHAR(255), \n\tprocessados INTEGER NOT NULL, \n\telegiveis INTEGER NOT NULL, \n\tbloqueados INTEGER NOT NULL, \n\tremovidos INTEGER NOT NULL, \n\tlease_token UUID, \n\tlease_ate TIMESTAMP WITH TIME ZONE, \n\terro VARCHAR(255), \n\tcorte_em TIMESTAMP WITH TIME ZONE NOT NULL, \n\tcriado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tatualizado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id), \n\tCHECK (status IN ('PENDENTE','PROCESSANDO','CONCLUIDA','FALHOU','CANCELADA')), \n\tCONSTRAINT uq_retencao_operacao UNIQUE (usuario_id, operacao_id)\n)\n\n",
    "\nCREATE TABLE logs_requisicoes (\n\tid UUID NOT NULL, \n\trequest_id VARCHAR(64) NOT NULL, \n\tcategoria VARCHAR(30) NOT NULL, \n\tmetodo VARCHAR(10) NOT NULL, \n\trota VARCHAR(255) NOT NULL, \n\tstatus INTEGER NOT NULL, \n\tduracao_ms INTEGER NOT NULL, \n\tcriado_em TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, \n\tPRIMARY KEY (id)\n)\n\n",
    "CREATE INDEX ix_auditoria_geral_acao ON auditoria_geral (acao)",
    "CREATE INDEX ix_auditoria_geral_criado_em ON auditoria_geral (criado_em)",
    "CREATE INDEX ix_auditoria_geral_instrumento_id ON auditoria_geral (instrumento_id)",
    "CREATE INDEX ix_auditoria_geral_operacao_id ON auditoria_geral (operacao_id)",
    "CREATE INDEX ix_auditoria_geral_request_id ON auditoria_geral (request_id)",
    "CREATE INDEX ix_auditoria_geral_usuario_id ON auditoria_geral (usuario_id)",
    "CREATE INDEX ix_exportacoes_criado_em ON exportacoes (criado_em)",
    "CREATE INDEX ix_exportacoes_expira_em ON exportacoes (expira_em)",
    "CREATE INDEX ix_exportacoes_instrumento_id ON exportacoes (instrumento_id)",
    "CREATE INDEX ix_exportacoes_lease ON exportacoes (status, lease_ate)",
    "CREATE INDEX ix_exportacoes_status ON exportacoes (status)",
    "CREATE INDEX ix_exportacoes_usuario_id ON exportacoes (usuario_id)",
    "CREATE INDEX ix_politicas_retencao_categoria ON politicas_retencao (categoria)",
    "CREATE INDEX ix_politicas_retencao_instrumento_id ON politicas_retencao (instrumento_id)",
    "CREATE INDEX ix_execucoes_retencao_politica_id ON execucoes_retencao (politica_id)",
    "CREATE INDEX ix_execucoes_retencao_status ON execucoes_retencao (status)",
    "CREATE INDEX ix_logs_requisicoes_categoria ON logs_requisicoes (categoria)",
    "CREATE INDEX ix_logs_requisicoes_criado_em ON logs_requisicoes (criado_em)",
    "CREATE INDEX ix_logs_requisicoes_request_id ON logs_requisicoes (request_id)"
]
