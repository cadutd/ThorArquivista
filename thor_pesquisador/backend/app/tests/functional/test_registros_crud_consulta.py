import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.main import create_app
from app.models.editorial import AcessoInstrumento, Papel
from app.models.user import Usuario
from app.services.auth_service import create_session
from app.tests.functional.test_editorial import ctx


def test_paginacao_total_ordem_busca_e_exclusao(ctx):
    client, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid + "/registros"
    ids = [rid]
    for n in range(4):
        response = client.post(base, json={"dados": {"titulo": "Consulta " + str(n)},
                                          "status": "INATIVO" if n == 0 else "ATIVO"})
        assert response.status_code == 201, response.text
        ids.append(response.json()["id"])
    first = client.post(base + "/consultar", json={"limit": 2}).json()
    second = client.post(base + "/consultar", json={"limit": 2, "offset": 2}).json()
    last = client.post(base + "/consultar", json={"limit": 2, "offset": 4}).json()
    assert first["total"] == second["total"] == last["total"] == 5
    assert (first["limit"], first["offset"]) == (2, 0)
    found = first["items"] + second["items"] + last["items"]
    assert len({row["id"] for row in found}) == 5
    assert {row["id"] for row in found} == set(ids)
    assert [(row["criado_em"], row["id"]) for row in found] == sorted(
        [(row["criado_em"], row["id"]) for row in found], reverse=True)
    page = client.post(base + "/consultar", json={"q": "  consulta ", "limit": 2, "offset": 2}).json()
    assert page["total"] == 4 and len(page["items"]) == 2
    assert all("Consulta" in row["dados"]["titulo"] for row in page["items"])
    inactive = client.post(base + "/consultar", json={"q": "Consulta", "status": "INATIVO"}).json()
    assert inactive["total"] == 1 and inactive["items"][0]["id"] == ids[1]
    assert client.delete(base + "/" + ids[1]).status_code == 200
    assert client.post(base + "/consultar", json={}).json()["total"] == 4
    assert registros_collection().find_one({"_id": ids[1]})["status"] == "EXCLUIDO"
    empty = client.post(base + "/consultar", json={"q": "inexistente"}).json()
    assert empty["total"] == 0 and empty["items"] == []
    beyond = client.post(base + "/consultar", json={"offset": 999}).json()
    assert beyond["total"] == 4 and beyond["items"] == []
    # The legacy cursor contract remains available to other callers.
    legacy = client.get(base, params={"page_size": 2}).json()
    assert legacy["next_cursor"] and legacy["has_more"]


@pytest.mark.parametrize("tipo,value,query", [
    ("TEXTO_CURTO", "Chegada [Lisboa]", "[lisboa]"),
    ("TEXTO_LONGO", "Historico de CHEGADA", "chegada"),
    ("URL", "https://example.org/acervo", "example.org"),
    ("NUMERO", 12.5, 12.5),
    ("BOOLEANO", False, False),
    ("DATA", "1900-01-02", "1900-01-02"),
    ("LISTA_SIMPLES", "Santos", "Santos"),
    ("LISTA_MULTIPLA", ["Santos", "Rio"], ["Rio"]),
])
def test_filtros_metadados_tipados(ctx, tipo, value, query):
    client, iid, _ = ctx
    path = "/api/v1/instrumentos/" + iid
    field = client.post(path + "/campos", json={"nome": "Filtro", "chave": "filtro", "tipo": tipo})
    assert field.status_code == 201, field.text
    record = client.post(path + "/registros", json={"dados": {"titulo": "Especial", "filtro": value}})
    assert record.status_code == 201, record.text
    page = client.post(path + "/registros/consultar", json={"filtros": {"filtro": query}, "q": "especial"})
    assert page.status_code == 200, page.text
    assert page.json()["total"] == 1
    assert page.json()["items"][0]["id"] == record.json()["id"]
    assert client.post(path + "/registros/consultar", json={"filtros": {"filtro": None}}).json()["total"] == 2


@pytest.mark.parametrize("payload", [
    {"limit": 0}, {"limit": 101}, {"offset": -1}, {"status": "EXCLUIDO"},
    {"filtros": {"$where": "true"}}, {"filtros": {"dados.titulo": "A"}},
    {"filtros": {"titulo": {"$ne": None}}}, {"q": "x" * 1001},
])
def test_consulta_rejeita_parametros_invalidos(ctx, payload):
    client, iid, _ = ctx
    response = client.post("/api/v1/instrumentos/" + iid + "/registros/consultar", json=payload)
    assert response.status_code == 422, response.text


def test_consulta_permissao_escopo_e_filtro_revogado(ctx):
    admin, iid, _ = ctx
    base = "/api/v1/instrumentos/" + iid
    anonymous = TestClient(create_app())
    assert anonymous.post(base + "/registros/consultar", json={}).status_code == 401
    with SessionLocal() as db:
        user = Usuario(nome="Consulta de registros " + uuid.uuid4().hex)
        role = Papel(nome="REG_" + uuid.uuid4().hex, permissoes=["registros_consultar"])
        db.add_all([user, role]); db.flush()
        grant = AcessoInstrumento(usuario_id=user.id, papel=role.nome, instrumento_id=uuid.UUID(iid))
        db.add(grant); db.commit()
        token, grant_id = create_session(db, user), grant.id
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    assert client.post(base + "/registros/consultar", json={}).status_code == 200
    assert client.post("/api/v1/instrumentos/" + str(uuid.uuid4()) + "/registros/consultar", json={}).status_code == 403
    fields = admin.get(base + "/campos").json()
    title = next(c for c in fields if c["chave"] == "titulo")
    assert admin.put(base + "/campos/" + title["id"], json={"aparece_busca": False}).status_code == 200
    assert client.post(base + "/registros/consultar", json={"filtros": {"titulo": "A"}}).status_code == 422
    with SessionLocal() as db:
        db.delete(db.get(AcessoInstrumento, grant_id)); db.commit()
    assert client.post(base + "/registros/consultar", json={}).status_code == 403


def test_consulta_isola_instrumentos(ctx):
    admin, iid, _ = ctx
    other = admin.post("/api/v1/instrumentos", json={"nome": "Outro", "tipo": "CATALOGO"}).json()["id"]
    assert admin.post("/api/v1/instrumentos/" + other + "/registros", json={"dados": {}}).status_code == 201
    page = admin.post("/api/v1/instrumentos/" + iid + "/registros/consultar", json={}).json()
    assert page["total"] == 1
    assert all(row["instrumento_id"] == iid for row in page["items"])
