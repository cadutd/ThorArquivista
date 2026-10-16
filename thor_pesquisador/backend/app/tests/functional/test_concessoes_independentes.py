import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.api.deps import db_dep
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import create_app
from app.models.editorial import AcessoInstrumento, Papel
from app.models.user import Usuario
from app.services.auth_service import create_session, usuario_from_claims
from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_usuarios import payload, criar, autenticado


def test_cadastro_e_edicao_nao_atribuem_perfis(ctx):
    admin, instrument, _ = ctx
    data = payload()
    user = criar(admin, data)
    client = autenticado(user["id"])
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/auth/permissoes").json() == {"permissoes": [], "escopos": {}}
    assert client.get("/api/v1/instrumentos/" + instrument).status_code == 403
    assert user["perfis"] == [] and user["total_acessos"] == 0 and not user["tem_acesso"]
    assert "perfil_codigo" not in user and "perfil_nome" not in user
    with SessionLocal() as db:
        linked = usuario_from_claims(db, {"sub": data["cpf"]})
        assert str(linked.id) == user["id"]
    assert admin.post("/api/v1/usuarios", json={**payload(), "perfil_codigo": "ADMIN"}).status_code == 422
    assert admin.put("/api/v1/usuarios/" + user["id"], json={**data, "perfil_codigo": "ADMIN"}).status_code == 422
    grant = admin.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": "EDITOR",
                                              "instrumento_id": instrument}).json()["id"]
    before = admin.get("/api/v1/acessos/" + grant).json()
    assert admin.put("/api/v1/usuarios/" + user["id"], json={**data, "nome": "Identidade atualizada"}).status_code == 200
    after = admin.get("/api/v1/acessos/" + grant).json()
    assert {k: v for k, v in after.items() if k != "nome"} == {k: v for k, v in before.items() if k != "nome"}
    assert client.get("/api/v1/instrumentos/" + instrument).status_code == 200
    detail = admin.get("/api/v1/usuarios/" + user["id"]).json()
    assert detail["tem_acesso"] and detail["perfis"][0]["codigo"] == "EDITOR"
    assert admin.delete("/api/v1/acessos/" + grant).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.get("/api/v1/auth/permissoes").json()["permissoes"] == []
    assert not admin.get("/api/v1/usuarios/" + user["id"]).json()["tem_acesso"]


def test_cadastrar_usuario_nao_exige_administrar_concessoes(ctx):
    admin, _, _ = ctx
    operator = criar(admin, payload())
    code = "CAD_" + uuid.uuid4().hex.upper()
    assert admin.post("/api/v1/perfis", json={"codigo": code, "nome": "Somente cadastro",
                                             "permissoes": ["usuarios_incluir"]}).status_code == 201
    assert admin.post("/api/v1/acessos", json={"usuario_id": operator["id"], "papel": code}).status_code == 201
    client = autenticado(operator["id"])
    user = criar(client, payload())
    assert not user["tem_acesso"] and not user["perfis"]
    assert client.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": "EDITOR"}).status_code == 403
    assert client.get("/api/v1/perfis").status_code == 403


def test_concessao_legada_nao_tem_prioridade_ou_escopo_obrigatorio(ctx):
    admin, instrument, _ = ctx
    user = criar(admin, payload())
    grant = admin.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": "EDITOR"}).json()["id"]
    with SessionLocal() as db:
        db.get(AcessoInstrumento, uuid.UUID(grant)).origem = "USUARIO"
        db.commit()
    assert admin.put("/api/v1/acessos/" + grant, json={"usuario_id": user["id"], "papel": "EDITOR",
                                                      "instrumento_id": instrument}).status_code == 200
    assert admin.get("/api/v1/usuarios/" + user["id"]).json()["total_acessos"] == 1
    assert admin.delete("/api/v1/acessos/" + grant).status_code == 200
    assert not admin.get("/api/v1/usuarios/" + user["id"]).json()["tem_acesso"]


def test_migration_e_revogacoes_concorrentes_preservam_ultimo_admin(monkeypatch):
    url = make_url(settings.database_url)
    assert url.database.endswith("_test")
    name = "concessoes_" + uuid.uuid4().hex + "_test"
    control = create_engine(url, isolation_level="AUTOCOMMIT")
    engine = None
    with control.connect() as connection:
        connection.execute(text('CREATE DATABASE "' + name + '"'))
    try:
        temporary_url = url.set(database=name)
        monkeypatch.setattr(settings, "database_url", temporary_url.render_as_string(hide_password=False))
        config = Config("alembic.ini")
        command.upgrade(config, "20261013_000009")
        engine = create_engine(temporary_url)
        with Session(engine) as db:
            db.add(Papel(nome="LEGACY_ADMIN", titulo="Administrador legado", permissoes=["*"], ativo=True))
            users = [Usuario(nome="Administrador " + str(i), username="admin" + str(i),
                             cpf=cpf, email="admin" + str(i) + "@example.org", ativo=True)
                     for i, cpf in enumerate(["52998224725", "11144477735"])]
            db.add_all(users); db.flush()
            grants = [AcessoInstrumento(usuario_id=user.id, papel="LEGACY_ADMIN", origem="USUARIO") for user in users]
            db.add_all(grants); db.commit()
            ids = [str(grant.id) for grant in grants]
            user_ids = [str(user.id) for user in users]
        with engine.connect() as connection:
            before = connection.execute(text("SELECT * FROM acessos_instrumento ORDER BY id")).all()
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT * FROM acessos_instrumento ORDER BY id")).all() == before
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == ScriptDirectory.from_config(config).get_current_head()
        with Session(engine) as db:
            tokens = [create_session(db, db.get(Usuario, uuid.UUID(uid))) for uid in user_ids]
        app = create_app()
        def isolated_db():
            with Session(engine) as db:
                yield db
        app.dependency_overrides[db_dep] = isolated_db
        clients = [TestClient(app), TestClient(app)]
        for client, token in zip(clients, tokens):
            client.cookies.set(settings.session_cookie_name, token)
        barrier = Barrier(2)
        def revoke(index):
            barrier.wait(timeout=10)
            return clients[index].delete("/api/v1/acessos/" + ids[index])
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(revoke, range(2)))
        assert sorted(r.status_code for r in responses) == [200, 409]
        survivor = next(i for i, response in enumerate(responses) if response.status_code == 409)
        assert "ultimo administrador" in responses[survivor].json()["detail"]
        client = clients[survivor]
        assert client.put("/api/v1/acessos/" + ids[survivor], json={
            "usuario_id": user_ids[survivor], "papel": "EDITOR"}).status_code == 409
        assert client.delete("/api/v1/perfis/LEGACY_ADMIN").status_code == 409
        assert client.get("/api/v1/perfis/LEGACY_ADMIN").json()["ativo"]
        assert client.delete("/api/v1/usuarios/" + user_ids[survivor]).status_code == 409
        with Session(engine) as db:
            assert db.scalar(select(AcessoInstrumento.id)) is not None
    finally:
        if engine:
            engine.dispose()
        with control.connect() as connection:
            connection.execute(text('DROP DATABASE "' + name + '" WITH (FORCE)'))
        control.dispose()
