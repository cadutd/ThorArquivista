import json
import uuid
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.core.config import settings


def test_upgrade_preserva_sessoes_e_downgrade_nao_descarta_visitantes(monkeypatch):
    url = make_url(settings.database_url)
    assert url.database.endswith("_test")
    name = "fase6_" + uuid.uuid4().hex + "_test"
    assert name.startswith("fase6_") and name.endswith("_test")
    control = create_engine(url, isolation_level="AUTOCOMMIT")
    engine = None
    with control.connect() as conn:
        conn.execute(text('CREATE DATABASE "' + name + '"'))
    try:
        temporary = url.set(database=name)
        monkeypatch.setattr(settings, "database_url", temporary.render_as_string(hide_password=False))
        config = Config("alembic.ini")
        command.upgrade(config, "20261015_000013")
        engine = create_engine(temporary)
        uid, sid, guest = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO usuarios(id,nome,username) VALUES(:id,'Usuario legado',:username)"),
                         {"id":uid,"username":"legado_"+uuid.uuid4().hex})
            conn.execute(text("INSERT INTO sessoes(id,usuario_id,token_hash,expira_em) VALUES(:id,:user,'token-legado',CURRENT_TIMESTAMP + INTERVAL '1 hour')"), {"id":sid,"user":uid})
            conn.execute(text("UPDATE papeis SET permissoes='[\"instrumentos_consultar\"]' WHERE nome='EDITOR'"))
        command.upgrade(config, "20261016_000014")
        instrument = uuid.uuid4()
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO instrumentos(id,nome,tipo) VALUES(:id,'Contagem legada','CATALOGO')"), {"id":instrument})
            for session in ("counter-first", "counter-second"):
                conn.execute(text("INSERT INTO portal_acessos(sessao_chave,instrumento_id,dia) VALUES(:session,:id,CURRENT_DATE)"),
                    {"session":session,"id":instrument})
        command.upgrade(config, "head")
        with engine.begin() as conn:
            assert conn.scalar(text("SELECT usuario_id FROM sessoes WHERE id=:id"), {"id":sid}) == uid
            assert conn.scalar(text("SELECT permissoes FROM papeis WHERE nome='EDITOR'")) == ["instrumentos_consultar"]
            assert conn.scalar(text("SELECT nome_instituicao FROM configuracao_portal")) == "Thor Pesquisador"
            assert conn.scalar(text("SELECT quantidade FROM portal_contagens WHERE instrumento_id=:id"), {"id":instrument}) == 2
            conn.execute(text("INSERT INTO sessoes(id,cpf_consultivo,nome_consultivo,token_hash,expira_em) VALUES(:id,'52998224725','Visitante teste','guest-test',CURRENT_TIMESTAMP + INTERVAL '1 hour')"), {"id":guest})
        with pytest.raises(RuntimeError, match="sessoes consultivas"):
            command.downgrade(config, "20261015_000013")
        with engine.begin() as conn:
            assert conn.scalar(text("SELECT count(*) FROM sessoes WHERE id=:id"), {"id":guest}) == 1
            conn.execute(text("DELETE FROM sessoes WHERE id=:id"), {"id":guest})
        command.downgrade(config, "20261015_000013")
        with engine.connect() as conn:
            assert conn.scalar(text("SELECT usuario_id FROM sessoes WHERE id=:id"), {"id":sid}) == uid
    finally:
        if engine:
            engine.dispose()
        with control.connect() as conn:
            conn.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        control.dispose()
