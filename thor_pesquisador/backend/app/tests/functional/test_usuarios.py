import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.tests.functional.test_editorial import ctx
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import create_app
from app.models.editorial import AcessoInstrumento
from app.models.user import Sessao, Usuario
from app.services.auth_service import create_session, usuario_from_claims


def cpf_teste():
    base = str(uuid.uuid4().int % 1000000000).zfill(9)
    for length in (9, 10):
        digit = sum(int(base[i]) * (length + 1 - i) for i in range(length)) * 10 % 11
        base += str(0 if digit == 10 else digit)
    return base


def payload(**overrides):
    data = dict(nome="Usuario " + uuid.uuid4().hex, username="teste_" + uuid.uuid4().hex,
                cpf=cpf_teste(), email=uuid.uuid4().hex + "@example.org",
                perfil_codigo="CONSULTA_INTERNA", ativo=True, observacoes="Cadastro administrativo")
    data.update(overrides)
    return data


def criar(admin, data):
    response = admin.post("/api/v1/usuarios", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def autenticado(user_id):
    with SessionLocal() as db:
        token = create_session(db, db.get(Usuario, uuid.UUID(user_id)))
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    return client


def test_crud_usuario_preserva_escopos_e_historico(ctx):
    admin, instrument_id, _ = ctx
    data = payload(perfil_codigo="EDITOR")
    user = criar(admin, data)
    path = "/api/v1/usuarios/" + user["id"]
    assert not user["govbr_vinculado"] and user["cpf"] == data["cpf"]
    assert user["username"] == data["username"]
    grant = admin.post("/api/v1/acessos", json={"usuario_id":user["id"],
        "papel":"EDITOR","instrumento_id":instrument_id})
    assert grant.status_code == 201
    extra = admin.post("/api/v1/acessos",json={"usuario_id":user["id"],"papel":"CONSULTA_INTERNA"})
    assert extra.status_code == 201
    principal = next(a for a in admin.get("/api/v1/acessos",params={"usuario_id":user["id"]}).json()["items"]
                     if a["papel"] == "EDITOR" and not a["instrumento_id"])
    assert admin.put("/api/v1/acessos/" + principal["id"],json={
        "usuario_id":user["id"],"papel":"EDITOR","instrumento_id":instrument_id}).status_code == 409
    client = autenticado(user["id"])
    updated = {**data,"nome":"Atualizado " + uuid.uuid4().hex,"perfil_codigo":"REVISOR"}
    assert admin.put(path,json=updated).status_code == 200
    permissions = client.get("/api/v1/auth/permissoes").json()
    assert "revisar" in permissions["permissoes"]
    assert "registros_editar" in permissions["escopos"][instrument_id]
    with SessionLocal() as db:
        assert db.get(AcessoInstrumento,uuid.UUID(extra.json()["id"])).origem == "MANUAL"
    filtered = admin.get("/api/v1/usuarios",params={"cpf":data["cpf"],"ativo":True,"limit":1}).json()
    assert filtered["total"] == 1 and filtered["items"][0]["perfil_nome"]
    assert admin.get("/api/v1/usuarios",params={"username":data["username"],"offset":1}).json()["items"] == []
    assert admin.delete(path).status_code == 200
    assert admin.get(path).status_code == 404
    assert client.get("/api/v1/auth/me").status_code == 401
    assert admin.get("/api/v1/usuarios",params={"q":data["username"]}).json()["total"] == 0
    assert admin.post("/api/v1/usuarios",json={**data,"username":"outra_" + uuid.uuid4().hex}).status_code == 409
    with SessionLocal() as db:
        retained = db.get(Usuario,uuid.UUID(user["id"]))
        assert retained.excluido_em and not retained.ativo and retained.cpf == data["cpf"]
        assert db.get(AcessoInstrumento,uuid.UUID(grant.json()["id"])) is not None
        assert db.scalar(select(func.count()).select_from(Sessao).where(Sessao.usuario_id == retained.id)) == 0


def test_duplicidade_validacao_e_autorizacao(ctx):
    admin, _, _ = ctx
    data = payload()
    user = criar(admin,data)
    assert admin.post("/api/v1/usuarios",json={**data,"username":"outro_" + uuid.uuid4().hex}).status_code == 409
    assert admin.post("/api/v1/usuarios",json={**payload(),"username":data["username"].upper()}).status_code == 409
    for invalid in [{"cpf":"00000000000"},{"email":"invalido"},{"username":"a"},{"nome":" "},
                    {"perfil_codigo":"INEXISTENTE"},{"govbr_sub":data["cpf"]},{"username":"com espaco"}]:
        assert admin.post("/api/v1/usuarios",json={**payload(),**invalid}).status_code == 422
    client = autenticado(user["id"])
    for method, path in [("post","/usuarios"),("put","/usuarios/" + user["id"]),("delete","/usuarios/" + user["id"])]:
        args = {"json":data} if method != "delete" else {}
        assert getattr(client,method)("/api/v1" + path,**args).status_code == 403
    assert client.get("/api/v1/usuarios/" + user["id"]).status_code == 403
    assert TestClient(create_app()).post("/api/v1/usuarios",json=data).status_code == 401


def test_desativacao_e_reativacao_revogam_sessoes(ctx):
    admin, _, _ = ctx
    data = payload()
    user = criar(admin,data)
    client = autenticado(user["id"])
    path = "/api/v1/usuarios/" + user["id"]
    assert admin.put(path,json={**data,"ativo":False}).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert admin.post("/api/v1/acessos",json={"usuario_id":user["id"],"papel":"EDITOR"}).status_code == 422
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as session_denied:
            create_session(db,db.get(Usuario,uuid.UUID(user["id"])))
        assert session_denied.value.status_code == 403
        with pytest.raises(HTTPException) as denied:
            usuario_from_claims(db,{"sub":data["cpf"]})
        assert denied.value.status_code == 403
    assert admin.put(path,json=data).status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert autenticado(user["id"]).get("/api/v1/auth/me").status_code == 200


def test_govbr_vincula_apenas_usuario_cadastrado_sem_sobrescrever_dados(ctx):
    admin, _, _ = ctx
    data = payload()
    user = criar(admin,data)
    with SessionLocal() as db:
        original_count = db.scalar(select(func.count()).select_from(Usuario))
        with pytest.raises(HTTPException) as denied:
            usuario_from_claims(db,{"sub":cpf_teste()})
        assert denied.value.status_code == 403
        assert db.scalar(select(func.count()).select_from(Usuario)) == original_count
        row = usuario_from_claims(db,{"sub":data["cpf"],"preferred_username":data["cpf"],
                                     "name":"Nome do provedor","email":"provider@example.org"})
        assert str(row.id) == user["id"] and row.nome == data["nome"] and row.email == data["email"]
        assert row.govbr_sub == data["cpf"]
        again = usuario_from_claims(db,{"sub":data["cpf"]})
        assert again.id == row.id
    linked = admin.get("/api/v1/usuarios/" + user["id"]).json()
    assert linked["govbr_vinculado"]
    assert admin.put("/api/v1/usuarios/" + user["id"],json={**data,"cpf":cpf_teste()}).status_code == 409
    assert admin.put("/api/v1/usuarios/" + user["id"],json={**data,"nome":"Atualizado local"}).status_code == 200
    admin.delete("/api/v1/usuarios/" + user["id"])
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as denied:
            usuario_from_claims(db,{"sub":data["cpf"]})
        assert denied.value.status_code == 403


@pytest.mark.parametrize("claims", [{"sub":"00000000000"},{"sub":"abc"},{"sub":"52998224725","preferred_username":"11144477735"},{}])
def test_govbr_rejeita_identidade_invalida(claims):
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as denied:
            usuario_from_claims(db,claims)
        assert denied.value.status_code == 401


def test_callback_valida_nonce_e_cadastro(ctx,monkeypatch):
    admin, _, _ = ctx
    data = payload()
    user = criar(admin,data)
    from app.api.v1 import auth
    claims = {"sub":data["cpf"],"nonce":"nonce-correto"}
    async def exchange(*args):
        return claims
    monkeypatch.setattr(auth,"exchange_code_for_claims",exchange)
    client = TestClient(create_app())
    client.cookies.set("thor_auth_state","state-correto")
    client.cookies.set("thor_auth_verifier","verifier")
    client.cookies.set("thor_auth_nonce","nonce-errado")
    path = "/api/v1/auth/govbr/callback?state=state-correto&code=code"
    assert client.get(path,follow_redirects=False).status_code == 401
    client.cookies.set("thor_auth_nonce","nonce-correto")
    response = client.get(path,follow_redirects=False)
    assert response.status_code == 307
    assert client.get("/api/v1/auth/me").json()["id"] == user["id"]
    assert client.get(path.replace("state-correto","state-incorreto"),follow_redirects=False).status_code == 400


def test_autoprotecao_e_perfil_principal_global(ctx):
    admin, _, _ = ctx
    data = payload(username="admin_" + uuid.uuid4().hex,perfil_codigo="ADMIN")
    user = criar(admin,data)
    client = autenticado(user["id"])
    path = "/api/v1/usuarios/" + user["id"]
    assert client.delete(path).status_code == 409
    assert client.put(path,json={**data,"ativo":False}).status_code == 409
    assert client.put(path,json={**data,"perfil_codigo":"EDITOR"}).status_code == 409
    grants = admin.get("/api/v1/acessos",params={"usuario_id":user["id"]}).json()["items"]
    assert client.delete("/api/v1/acessos/" + grants[0]["id"]).status_code == 409
    with SessionLocal() as db:
        from app.editorial_cli import cadastrar_admin_inicial
        from app.schemas.usuario import UsuarioIn
        with pytest.raises(ValueError,match="administrador ativo"):
            cadastrar_admin_inicial(db,UsuarioIn(**payload(perfil_codigo="ADMIN")))
