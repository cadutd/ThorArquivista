"""Remove primary-profile semantics without changing existing access grants."""
from alembic import op
import sqlalchemy as sa

revision = "20261014_000010"
down_revision = "20261013_000009"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("uq_acesso_principal", table_name="acessos_instrumento")
    op.drop_constraint("ck_acesso_origem", "acessos_instrumento", type_="check")
    # Origin remains historical provenance, not an authorization hierarchy.
    op.create_check_constraint("ck_acesso_origem", "acessos_instrumento",
                               "origem IN ('MANUAL', 'USUARIO')")


def downgrade():
    connection = op.get_bind()
    invalid = connection.scalar(sa.text("""SELECT EXISTS(
        SELECT 1 FROM acessos_instrumento WHERE origem='USUARIO' AND instrumento_id IS NOT NULL
        UNION ALL
        SELECT 1 FROM acessos_instrumento WHERE origem='USUARIO'
        GROUP BY usuario_id HAVING count(*) > 1)"""))
    if invalid:
        raise RuntimeError("Concessoes legadas incompativeis com perfil principal; revise antes do rollback.")
    op.drop_constraint("ck_acesso_origem", "acessos_instrumento", type_="check")
    op.create_check_constraint("ck_acesso_origem", "acessos_instrumento",
        "origem IN ('MANUAL', 'USUARIO') AND (origem <> 'USUARIO' OR instrumento_id IS NULL)")
    op.create_index("uq_acesso_principal", "acessos_instrumento", ["usuario_id"], unique=True,
                    postgresql_where=sa.text("origem = 'USUARIO'"))
