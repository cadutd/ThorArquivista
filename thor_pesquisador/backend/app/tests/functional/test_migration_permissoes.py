import uuid
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.permissions import expand_legacy


def test_migration_crud_preserva_perfis_usuarios_e_escopos(monkeypatch):
    url = make_url(settings.database_url)
    assert url.database.endswith("_test")
    name = "permissoes_migration_" + uuid.uuid4().hex + "_test"
    control = create_engine(url, isolation_level="AUTOCOMMIT")
    engine = None
    with control.connect() as connection:
        connection.execute(text('CREATE DATABASE "' + name + '"'))
    try:
        migrated_url = url.set(database=name)
        monkeypatch.setattr(settings, "database_url", migrated_url.render_as_string(hide_password=False))
        config = Config("alembic.ini")
        command.upgrade(config, "20261012_000008")
        engine = create_engine(migrated_url)
        user_id, instrument_id, grant_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        with engine.begin() as connection:
            connection.execute(text("""INSERT INTO papeis(nome,titulo,descricao,ativo,permissoes)
                VALUES('LEGADO_CRUD','Perfil legado','Preservar',false,
                       '["consultar","editar_registro","gerenciar_imagens","codigo_customizado"]'::jsonb)"""))
            connection.execute(text("""INSERT INTO usuarios(id,nome,username,ativo)
                VALUES(:id,'Usuario preservado','migration_crud',true)"""), {"id": user_id})
            connection.execute(text("""INSERT INTO instrumentos(id,nome,tipo,visibilidade,status)
                VALUES(:id,'Instrumento preservado','CATALOGO','INTERNO','RASCUNHO')"""), {"id": instrument_id})
            connection.execute(text("""INSERT INTO acessos_instrumento(id,usuario_id,papel,instrumento_id,origem)
                VALUES(:id,:user,'LEGADO_CRUD',:instrument,'MANUAL')"""),
                {"id": grant_id, "user": user_id, "instrument": instrument_id})
            before = connection.execute(text("SELECT nome,permissoes FROM papeis")).all()
        command.upgrade(config, "20261013_000009")
        with engine.connect() as connection:
            after = dict(connection.execute(text("SELECT nome,permissoes FROM papeis")).all())
            assert set(after) == {code for code, _ in before}
            for code, permissions in before:
                assert after[code] == expand_legacy(permissions)
            row = connection.execute(text("SELECT titulo,descricao,ativo FROM papeis WHERE nome='LEGADO_CRUD'")).one()
            assert tuple(row) == ("Perfil legado", "Preservar", False)
            row = connection.execute(text("SELECT id,usuario_id,papel,instrumento_id,origem FROM acessos_instrumento")).one()
            assert tuple(row) == (grant_id, user_id, "LEGADO_CRUD", instrument_id, "MANUAL")
            assert connection.scalar(text("SELECT count(*) FROM usuarios WHERE id=:id"), {"id": user_id}) == 1
            assert after["ADMIN"] == ["*"]
            assert not any(p.startswith(("usuarios_", "perfis_", "acessos_", "permissoes_"))
                           for p in after["EDITOR"])
        with pytest.raises(RuntimeError, match="escalada"):
            command.downgrade(config, "20261012_000008")
    finally:
        if engine:
            engine.dispose()
        with control.connect() as connection:
            connection.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        control.dispose()
