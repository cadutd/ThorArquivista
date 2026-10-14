import uuid
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.tests.functional.test_editorial import ctx
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import create_app
from app.models.editorial import AcessoInstrumento
from app.models.user import Usuario
from app.services.auth_service import create_session


def user_client():
    with SessionLocal() as db:
        user = Usuario(govbr_sub="admin_test_" + uuid.uuid4().hex,
            nome="Usuario " + uuid.uuid4().hex, email=uuid.uuid4().hex + "@example.org")
        db.add(user); db.commit()
        data = {"id":str(user.id), "nome":user.nome, "email":user.email}
        token = create_session(db, user)
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    return client, data


def test_perfil_crud_escopo_desativacao_e_reativacao(ctx):
    admin, instrument_id, _ = ctx
    code = "TESTE_" + uuid.uuid4().hex.upper()
    payload = {"codigo":code, "nome":"Perfil de teste", "descricao":"Escopo controlado",
        "ativo":True, "permissoes":["imagens_incluir","instrumentos_consultar"]}
    response = admin.post("/api/v1/perfis", json=payload)
    assert response.status_code == 201, response.text
    assert admin.post("/api/v1/perfis", json=payload).status_code == 409
    assert admin.get("/api/v1/perfis?q=" + code).json()["total"] == 1
    assert admin.get("/api/v1/perfis?q=" + code + "&offset=1").json()["items"] == []
    client, user = user_client()
    grant = admin.post("/api/v1/acessos", json={
        "usuario_id":user["id"], "papel":code, "instrumento_id":instrument_id})
    assert grant.status_code == 201
    assert client.get("/api/v1/instrumentos/" + instrument_id).status_code == 200
    assert client.get("/api/v1/auth/permissoes").json()["escopos"][instrument_id] == ["imagens_incluir","instrumentos_consultar"]
    assert admin.put("/api/v1/perfis/" + code, json={**payload,"ativo":False}).status_code == 200
    assert client.get("/api/v1/instrumentos/" + instrument_id).status_code == 403
    assert client.get("/api/v1/instrumentos").json()["total"] == 0
    assert client.get("/api/v1/auth/permissoes").json()["escopos"] == {}
    assert client.post("/api/v1/imagens", json={"titulo":"Negada",
        "uri":"https://example.org/image.jpg", "direitos_acesso":"PUBLICO"}).status_code == 403
    assert admin.post("/api/v1/acessos", json={"usuario_id":user["id"], "papel":code}).status_code == 422
    assert admin.put("/api/v1/perfis/" + code, json=payload).status_code == 200
    assert client.get("/api/v1/instrumentos/" + instrument_id).status_code == 200
    assert admin.delete("/api/v1/perfis/" + code).json()["status"] == "desativado"
    with SessionLocal() as db:
        assert db.get(AcessoInstrumento, uuid.UUID(grant.json()["id"])) is not None
    assert client.get("/api/v1/instrumentos/" + instrument_id).status_code == 403
    admin.delete("/api/v1/acessos/" + grant.json()["id"])
    assert admin.delete("/api/v1/perfis/" + code).json()["status"] == "excluido"
    assert admin.get("/api/v1/perfis/" + code).status_code == 404


def test_protecao_admin_validacao_e_acesso_negado(ctx):
    admin, _, _ = ctx
    payload = {"codigo":"ADMIN", "nome":"Administrador", "permissoes":["*"]}
    assert admin.post("/api/v1/perfis", json=payload).status_code == 409
    assert admin.put("/api/v1/perfis/ADMIN", json=payload).status_code == 409
    assert admin.delete("/api/v1/perfis/ADMIN").status_code == 409
    for permissions in [["*"], ["permissao_inventada"]]:
        assert admin.post("/api/v1/perfis", json={**payload,"codigo":"INVALIDO","permissoes":permissions}).status_code == 422
    assert admin.put("/api/v1/perfis/EDITOR", json={**payload,"codigo":"RENOMEADO","permissoes":[]}).status_code == 409
    client, user = user_client()
    for path in ["/perfis","/permissoes","/usuarios","/usuarios/" + user["id"],"/acessos"]:
        assert client.get("/api/v1" + path).status_code == 403
    assert client.post("/api/v1/perfis", json={**payload,"codigo":"NOVO","permissoes":[]}).status_code == 403
    assert client.put("/api/v1/perfis/EDITOR", json={**payload,"codigo":"EDITOR","permissoes":[]}).status_code == 403
    assert client.delete("/api/v1/perfis/EDITOR").status_code == 403


def test_usuario_filtros_paginacao_e_concessoes(ctx):
    admin, instrument_id, _ = ctx
    _, user = user_client()
    admin.post("/api/v1/acessos", json={"usuario_id":user["id"],"papel":"CONSULTA_INTERNA","instrumento_id":instrument_id})
    users = admin.get("/api/v1/usuarios", params={"q":user["email"],"papel":"CONSULTA_INTERNA","limit":1}).json()
    assert users["total"] == 1 and users["items"][0]["total_acessos"] == 1
    assert "cpf" not in users["items"][0] and "govbr_sub" not in users["items"][0]
    assert admin.get("/api/v1/usuarios", params={"q":user["nome"],"offset":1}).json()["items"] == []
    assert admin.get("/api/v1/usuarios/" + user["id"]).json()["nome"] == user["nome"]
    grants = admin.get("/api/v1/acessos", params={"usuario_id":user["id"]}).json()
    assert grants["total"] == 1 and grants["items"][0]["usuario_id"] == user["id"]


def test_catalogo_permissoes_somente_leitura(ctx):
    admin, _, _ = ctx
    result = admin.get("/api/v1/permissoes", params={"q":"publicar","modulo":"Editorial","acao":"EDITAR","limit":1}).json()
    assert result["total"] == 1 and result["items"][0]["codigo"] == "publicar"
    assert admin.get("/api/v1/permissoes", params={"q":"publicar","offset":1}).json()["items"] == []
    assert admin.post("/api/v1/permissoes", json={}).status_code == 405
    assert admin.get("/api/v1/perfis?limit=101").status_code == 422
