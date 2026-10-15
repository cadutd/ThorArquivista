import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.main import create_app
from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_usuarios import payload, criar, autenticado

PATH = "/api/v1/acessos/lote"


def proposta(user, instrument_id=None, **overrides):
    return {"usuario_id": user["id"], "perfis": ["EDITOR", "REVISOR"],
            "escopo": "INSTRUMENTO" if instrument_id else "GLOBAL",
            "instrumento_ids": [instrument_id] if instrument_id else [], **overrides}


def acessos(admin, user):
    return admin.get("/api/v1/acessos", params={"usuario_id": user["id"], "limit": 100}).json()


def test_lote_multiplos_perfis_instrumentos_e_buscas(ctx):
    admin, instrument_id, _ = ctx
    user = criar(admin, payload())
    second = admin.post("/api/v1/instrumentos", json={"nome": "Lote " + uuid.uuid4().hex, "tipo": "GUIA"}).json()
    for field in ("nome", "username", "email"):
        result = admin.get("/api/v1/usuarios", params={field: user[field], "ativo": True}).json()
        assert result["total"] == 1 and result["items"][0]["id"] == user["id"]
    query = {"nome": second["nome"], "tipo": "GUIA", "status": "RASCUNHO", "limit": 1}
    assert admin.get("/api/v1/instrumentos", params=query).json()["items"][0]["id"] == second["id"]
    assert admin.get("/api/v1/instrumentos", params={**query, "tipo": "CATALOGO"}).json()["total"] == 0
    assert admin.get("/api/v1/instrumentos", params={**query, "status": "PUBLICADO"}).json()["total"] == 0
    assert admin.get("/api/v1/instrumentos", params={**query, "offset": 1}).json()["items"] == []
    assert admin.get("/api/v1/instrumentos", params={"tipo": "INVALIDO"}).status_code == 422
    response = admin.post(PATH, json=proposta(user, instrument_id, instrumento_ids=[instrument_id, second["id"]]))
    assert response.status_code == 201, response.text
    assert response.json()["total"] == 4
    assert {(r["papel"], r["instrumento_id"]) for r in acessos(admin, user)["items"]} == {
        (p, i) for p in ("EDITOR", "REVISOR") for i in (instrument_id, second["id"])}
    effective = autenticado(user["id"]).get("/api/v1/auth/permissoes").json()
    assert not effective["permissoes"]
    assert set(effective["escopos"]) == {instrument_id, second["id"]}


@pytest.mark.parametrize("override", [
    {"perfis": []}, {"perfis": ["EDITOR", "EDITOR"]}, {"perfis": [""]},
    {"escopo": "INVALIDO"}, {"escopo": "GLOBAL", "instrumento_ids": [str(uuid.uuid4())]},
    {"escopo": "INSTRUMENTO"}, {"escopo": "INSTRUMENTO", "instrumento_ids": [str(uuid.UUID(int=1))]*2},
    {"perfis": ["EDITOR"]*51}, {"instrumento_ids": [str(uuid.uuid4()) for _ in range(101)]},
    {"escopo": "INSTRUMENTO", "perfis": ["P_" + str(n) for n in range(50)],
     "instrumento_ids": [str(uuid.uuid4()) for _ in range(21)]},
    {"inesperado": True},
])
def test_lote_schema_nao_grava(ctx, override):
    admin, _, _ = ctx
    user = criar(admin, payload())
    response = admin.post(PATH, json=proposta(user, **override))
    assert response.status_code == 422, response.text
    assert acessos(admin, user)["total"] == 0


@pytest.mark.parametrize("case", ["usuario", "inativo", "perfil", "perfil_inativo", "instrumento", "admin"])
def test_lote_referencias_e_estados_atomicos(ctx, case):
    admin, instrument_id, _ = ctx
    user = criar(admin, payload(ativo=case != "inativo"))
    data = proposta(user, instrument_id)
    expected = 422
    if case == "usuario":
        data["usuario_id"] = str(uuid.uuid4()); expected = 404
    elif case == "perfil":
        data["perfis"].append("INEXISTENTE")
    elif case == "perfil_inativo":
        code = "INATIVO_" + uuid.uuid4().hex[:12].upper()
        assert admin.post("/api/v1/perfis", json={"codigo": code, "nome": code, "ativo": False,
                                               "permissoes": ["instrumentos_consultar"]}).status_code == 201
        data["perfis"].append(code)
    elif case == "instrumento":
        data["instrumento_ids"].append(str(uuid.uuid4())); expected = 404
    elif case == "admin":
        data["perfis"].append("ADMIN")
    response = admin.post(PATH, json=data)
    assert response.status_code == expected, response.text
    assert acessos(admin, user)["total"] == 0


@pytest.mark.parametrize("existing_global,new_global", [(False, False), (True, False), (False, True), (True, True)])
def test_lote_conflitos_preservam_tudo(ctx, existing_global, new_global):
    admin, instrument_id, _ = ctx
    user = criar(admin, payload())
    response = admin.post("/api/v1/acessos", json={"usuario_id": user["id"], "papel": "EDITOR",
        "instrumento_id": None if existing_global else instrument_id})
    assert response.status_code == 201
    before = acessos(admin, user)
    response = admin.post(PATH, json=proposta(user, None if new_global else instrument_id))
    assert response.status_code == 409, response.text
    assert acessos(admin, user) == before


def test_lote_global_e_reenvio(ctx):
    admin, _, _ = ctx
    user = criar(admin, payload())
    data = proposta(user)
    assert admin.post(PATH, json=data).json()["total"] == 2
    assert admin.post(PATH, json=data).status_code == 409
    assert acessos(admin, user)["total"] == 2
    assert all(r["instrumento_id"] is None for r in acessos(admin, user)["items"])


def test_lote_autorizacao_e_delegacao(ctx):
    admin, instrument_id, _ = ctx
    actor = criar(admin, payload())
    target = criar(admin, payload())
    client = autenticado(actor["id"])
    data = proposta(target, instrument_id)
    assert client.post(PATH, json=data).status_code == 403
    assert TestClient(create_app()).post(PATH, json=data).status_code == 401
    code = "LOTE_" + uuid.uuid4().hex[:12].upper()
    assert admin.post("/api/v1/perfis", json={"codigo": code, "nome": code,
        "permissoes": ["acessos_incluir", "instrumentos_consultar"]}).status_code == 201
    assert admin.post("/api/v1/acessos", json={"usuario_id": actor["id"], "papel": code}).status_code == 201
    assert client.post(PATH, json=data).status_code == 403
    assert acessos(admin, target)["total"] == 0
    assert client.post(PATH, json=proposta(target, instrument_id, perfis=["CONSULTA_INTERNA"])).status_code == 403


def test_lote_concorrente_nao_duplica(ctx):
    admin, instrument_id, _ = ctx
    user = criar(admin, payload())
    data = proposta(user, instrument_id)
    def submit(_):
        client = TestClient(create_app())
        client.cookies.update(admin.cookies)
        return client.post(PATH, json=data).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, range(2))) == [201, 409]
    assert acessos(admin, user)["total"] == 2


def test_lote_falha_sql_reverte_todas_as_linhas(ctx, monkeypatch):
    from app.models.editorial import AcessoInstrumento
    admin, instrument_id, _ = ctx
    user = criar(admin, payload())
    original = Session.flush
    def fail(db, *args, **kwargs):
        inserts = any(isinstance(row, AcessoInstrumento) for row in db.new)
        result = original(db, *args, **kwargs)
        if inserts:
            raise IntegrityError("falha simulada", {}, Exception("integridade"))
        return result
    with monkeypatch.context() as m:
        m.setattr(Session, "flush", fail)
        assert admin.post(PATH, json=proposta(user, instrument_id)).status_code == 409
    assert acessos(admin, user)["total"] == 0
