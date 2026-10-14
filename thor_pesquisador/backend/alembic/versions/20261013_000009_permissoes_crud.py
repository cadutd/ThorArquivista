"""Split CRUD permissions without changing users, roles or access scopes."""
from alembic import op
import sqlalchemy as sa

revision = "20261013_000009"
down_revision = "20261012_000008"
branch_labels = None
depends_on = None

LEGACY = {
    "consultar": [
        "instrumentos_consultar",
        "campos_consultar",
        "registros_consultar",
        "imagens_consultar",
        "galerias_consultar",
        "pesquisa_consultar",
        "editorial_consultar",
        "dashboard_consultar"
    ],
    "criar_instrumento": [
        "instrumentos_incluir"
    ],
    "gerenciar": [
        "instrumentos_editar",
        "instrumentos_excluir",
        "campos_incluir",
        "campos_editar",
        "campos_excluir"
    ],
    "editar_registro": [
        "registros_incluir",
        "registros_editar",
        "registros_excluir"
    ],
    "gerenciar_imagens": [
        "imagens_consultar",
        "imagens_incluir",
        "imagens_editar",
        "imagens_excluir",
        "galerias_consultar",
        "galerias_incluir",
        "galerias_editar",
        "galerias_excluir"
    ]
}


def upgrade():
    connection = op.get_bind()
    profiles = sa.table("papeis", sa.column("nome", sa.String), sa.column("permissoes", sa.JSON))
    for name, permissions in connection.execute(sa.select(profiles.c.nome, profiles.c.permissoes)):
        expanded = sorted({code for old in permissions for code in LEGACY.get(old, [old])})
        connection.execute(profiles.update().where(profiles.c.nome == name).values(permissoes=expanded))


def downgrade():
    # Granular grants cannot be collapsed without granting additional operations.
    raise RuntimeError("Downgrade requer revisao manual das permissoes para evitar escalada de privilegios.")
