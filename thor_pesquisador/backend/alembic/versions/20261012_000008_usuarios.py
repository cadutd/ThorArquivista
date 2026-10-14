"""Local registration and CPF identity; retain users and existing access scopes."""
from alembic import op
import sqlalchemy as sa

revision = "20261012_000008"
down_revision = "20261012_000007"
branch_labels = None
depends_on = None


def _cpf(value):
    value = (value or "").strip().replace(".", "").replace("-", "")
    if len(value) != 11 or not value.isascii() or not value.isdigit() or len(set(value)) == 1:
        return None
    for length in (9, 10):
        digit = sum(int(value[i]) * (length + 1 - i) for i in range(length)) * 10 % 11
        if int(value[length]) != (0 if digit == 10 else digit):
            return None
    return value


def upgrade():
    op.alter_column("usuarios", "govbr_sub", existing_type=sa.String(64), nullable=True)
    op.add_column("usuarios", sa.Column("username", sa.String(150)))
    op.add_column("usuarios", sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("usuarios", sa.Column("observacoes", sa.Text()))
    op.add_column("usuarios", sa.Column("excluido_em", sa.DateTime(timezone=True)))
    connection = op.get_bind()
    seen = set()
    rows = connection.execute(sa.text("SELECT id, cpf, govbr_sub FROM usuarios ORDER BY criado_em, id")).mappings().all()
    connection.execute(sa.text("UPDATE usuarios SET govbr_sub=NULL"))
    for row in rows:
        cpf = _cpf(row["cpf"]) or _cpf(row["govbr_sub"])
        # The existing reserved local development account is never a gov.br identity.
        development = row["govbr_sub"] == "00000000000"
        active = development or bool(cpf and cpf not in seen)
        original = row["cpf"]
        normalized = "00000000000" if development else cpf if active else None
        subject = row["govbr_sub"]
        linked = "00000000000" if development else normalized if active and _cpf(subject) == normalized else None
        note = None
        if not active or (subject and not linked):
            note = "Cadastro legado pendente de regularizacao. CPF: " + (original or "-") + "; identificador gov.br: " + (subject or "-")
        connection.execute(sa.text(
            "UPDATE usuarios SET username=:username, cpf=:cpf, govbr_sub=:linked, ativo=:ativo, observacoes=:note WHERE id=:id"),
            dict(id=row["id"], username="desenvolvimento" if development else "usuario_" + row["id"].hex,
                 cpf=normalized, linked=linked, ativo=active, note=note))
        if normalized:
            seen.add(normalized)
        if not active:
            connection.execute(sa.text("DELETE FROM sessoes WHERE usuario_id=:id"), {"id":row["id"]})
    op.alter_column("usuarios", "username", nullable=False)
    op.create_unique_constraint("uq_usuarios_username", "usuarios", ["username"])
    op.drop_index("ix_usuarios_cpf", table_name="usuarios")
    op.create_index("ix_usuarios_cpf", "usuarios", ["cpf"], unique=True)
    op.create_index("ix_usuarios_ativo", "usuarios", ["ativo"])
    op.add_column("acessos_instrumento", sa.Column("origem", sa.String(10), nullable=False, server_default="MANUAL"))
    op.execute("""UPDATE acessos_instrumento SET origem='USUARIO'
        WHERE instrumento_id IS NULL AND usuario_id IN
        (SELECT usuario_id FROM acessos_instrumento WHERE instrumento_id IS NULL
         GROUP BY usuario_id HAVING count(*)=1)""")
    op.create_index("uq_acesso_principal", "acessos_instrumento", ["usuario_id"], unique=True,
                    postgresql_where=sa.text("origem = 'USUARIO'"))
    op.create_check_constraint("ck_acesso_origem", "acessos_instrumento",
        "origem IN ('MANUAL', 'USUARIO') AND (origem <> 'USUARIO' OR instrumento_id IS NULL)")


def downgrade():
    op.drop_constraint("ck_acesso_origem", "acessos_instrumento", type_="check")
    op.drop_index("uq_acesso_principal", table_name="acessos_instrumento")
    op.drop_column("acessos_instrumento", "origem")
    op.drop_index("ix_usuarios_ativo", table_name="usuarios")
    op.drop_index("ix_usuarios_cpf", table_name="usuarios")
    op.create_index("ix_usuarios_cpf", "usuarios", ["cpf"])
    op.drop_constraint("uq_usuarios_username", "usuarios", type_="unique")
    for column in ("excluido_em", "observacoes", "ativo", "username"):
        op.drop_column("usuarios", column)
    op.execute("UPDATE usuarios SET govbr_sub='cadastro_local_' || id::text WHERE govbr_sub IS NULL")
    op.alter_column("usuarios", "govbr_sub", nullable=False)
