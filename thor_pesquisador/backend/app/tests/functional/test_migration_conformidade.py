"""Real PostgreSQL upgrade/rollback with legacy histories and a customized default role."""
import json
import uuid
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.core.config import settings


def test_migration_preserva_historicos_perfis_customizados_e_rollback(monkeypatch):
    url = make_url(settings.database_url)
    assert url.database.endswith("_test")
    name = "fase5_" + uuid.uuid4().hex + "_test"
    control = create_engine(url, isolation_level="AUTOCOMMIT")
    engine = None
    with control.connect() as conn:
        conn.execute(text('CREATE DATABASE "' + name + '"'))
    try:
        temporary = url.set(database=name)
        monkeypatch.setattr(settings, "database_url", temporary.render_as_string(hide_password=False))
        config = Config("alembic.ini")
        command.upgrade(config, "20261014_000010")
        engine = create_engine(temporary)
        image_event, editorial_event, author, iid = [uuid.uuid4() for _ in range(4)]
        with engine.begin() as conn:
            conn.execute(text("""INSERT INTO auditoria_imagens
                (id,usuario_id,acao,detalhe,criado_em) VALUES(:id,:author,'LEGADO','{}','2020-01-02T03:04:05Z')"""),
                {"id": image_event, "author": author})
            conn.execute(text("""INSERT INTO eventos_editoriais
                (id,instrumento_id,usuario_id,agente,acao,estado_anterior,estado_novo,versao,resultado,criado_em)
                VALUES(:id,:iid,:author,'Autor historico','editar','RASCUNHO','RASCUNHO',1,'{}','2020-01-02T03:04:05Z')"""),
                {"id": editorial_event, "iid": iid, "author": author})
            conn.execute(text("UPDATE papeis SET permissoes=CAST(:p AS JSONB) WHERE nome='GESTOR_INSTRUMENTOS'"),
                         {"p": json.dumps(["instrumentos_consultar"])})
            old_image = conn.execute(text("SELECT id,usuario_id,acao,detalhe,criado_em FROM auditoria_imagens")).all()
            old_editorial = conn.execute(text("SELECT id,usuario_id,agente,acao,criado_em FROM eventos_editoriais")).all()
            original_reviewer = conn.scalar(text("SELECT permissoes FROM papeis WHERE nome='REVISOR'"))
        command.upgrade(config, "head")
        with engine.connect() as conn:
            assert conn.execute(text("SELECT id,usuario_id,acao,detalhe,criado_em FROM auditoria_imagens")).all() == old_image
            assert conn.execute(text("SELECT id,usuario_id,agente,acao,criado_em FROM eventos_editoriais")).all() == old_editorial
            assert conn.scalar(text("SELECT permissoes FROM papeis WHERE nome='GESTOR_INSTRUMENTOS'")) == ["instrumentos_consultar"]
            assert {"auditoria_consultar", "relatorios_consultar"}.issubset(
                conn.scalar(text("SELECT permissoes FROM papeis WHERE nome='REVISOR'")))
        command.downgrade(config, "20261014_000010")
        with engine.connect() as conn:
            assert conn.execute(text("SELECT id,usuario_id,acao,detalhe,criado_em FROM auditoria_imagens")).all() == old_image
            assert conn.execute(text("SELECT id,usuario_id,agente,acao,criado_em FROM eventos_editoriais")).all() == old_editorial
            assert conn.scalar(text("SELECT permissoes FROM papeis WHERE nome='REVISOR'")) == original_reviewer
            assert conn.scalar(text("SELECT permissoes FROM papeis WHERE nome='GESTOR_INSTRUMENTOS'")) == ["instrumentos_consultar"]
    finally:
        if engine:
            engine.dispose()
        with control.connect() as conn:
            conn.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        control.dispose()
