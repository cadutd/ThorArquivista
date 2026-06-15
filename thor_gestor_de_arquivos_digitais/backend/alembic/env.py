from __future__ import annotations

from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db.base import Base  # noqa: F401
from app.core.config import settings
#from app.models import aip, event, job  # noqa: F401
from app.models import unidade_acondicionamento, unidade_acondicionamento_digital  # noqa: F401
from app.models import midia_armazenamento, copia_unidade_acondicionamento_digital  # noqa: F401
from app.models import evento_preservacao  # noqa: F401
from app.models import evento_midia_armazenamento  # noqa: F401
from app.models import armazenamento  # noqa: F401
from app.models import descricao_arquivistica  # noqa: F401
from app.models import instrumento_pesquisa  # noqa: F401
import alembic_postgresql_enum # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,  compare_type=True,)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
