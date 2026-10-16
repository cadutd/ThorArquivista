"""Indexes for bounded retention scans and scoped audit pages."""
from alembic import op

revision = "20261015_000013"
down_revision = "20261015_000012"
branch_labels = None
depends_on = None
INDEXES = {
    "ix_logs_retencao_lote": ("logs_requisicoes", "categoria, criado_em, id"),
    "ix_auditoria_escopo_data": ("auditoria_geral", "instrumento_id, criado_em DESC, id"),
    "ix_imagens_auditoria_escopo_data": ("auditoria_imagens", "instrumento_id, criado_em DESC, id"),
    "ix_retencao_lease": ("execucoes_retencao", "status, lease_ate"),
    "ix_editorial_expurgo": ("editorial_registros", "instrumento_id, status_operacional, atualizado_em, id"),
}


def upgrade():
    for name, (table, fields) in INDEXES.items():
        op.execute(f"CREATE INDEX {name} ON {table} ({fields})")


def downgrade():
    for name in reversed(INDEXES):
        op.drop_index(name)
