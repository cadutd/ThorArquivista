from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.db.mongo import registros_collection
from app.main import create_app


def unique_code() -> str:
    return uuid.uuid4().hex[:10]


def authenticated_client() -> TestClient:
    client = TestClient(create_app())
    response = client.post("/api/v1/auth/dev-login")
    assert response.status_code == 200
    return client


def instrumento_payload(code: str, **overrides):
    payload = {
        "nome": f"Instrumento funcional {code}",
        "tipo": "INVENTARIO",
        "descricao": "Criado por teste funcional.",
        "status": "RASCUNHO",
        "visibilidade": "INTERNO",
    }
    payload.update(overrides)
    return payload


def campo_payload(code: str, **overrides):
    payload = {
        "nome": f"Titulo {code}",
        "chave": f"titulo_{code}",
        "tipo": "TEXTO_CURTO",
        "ordem": 1,
        "obrigatorio": True,
        "multiplo": False,
        "aparece_cadastro": True,
        "aparece_listagem": True,
        "aparece_busca": True,
    }
    payload.update(overrides)
    return payload


def test_crud_instrumento_por_funcao():
    client = authenticated_client()
    code = unique_code()

    created = client.post("/api/v1/instrumentos", json=instrumento_payload(code))
    assert created.status_code == 201
    instrumento_id = created.json()["id"]

    invalid = client.post("/api/v1/instrumentos", json={"nome": ""})
    listed = client.get("/api/v1/instrumentos", params={"q": code})
    found = client.get(f"/api/v1/instrumentos/{instrumento_id}")
    dashboard = client.get("/api/v1/dashboard")
    updated = client.put(f"/api/v1/instrumentos/{instrumento_id}", json={"status": "PUBLICADO"})
    reindex = client.post(f"/api/v1/instrumentos/{instrumento_id}/reindexar")
    dashboard_after_reindex = client.get("/api/v1/dashboard")
    deleted = client.delete(f"/api/v1/instrumentos/{instrumento_id}")
    missing_delete = client.delete(f"/api/v1/instrumentos/{instrumento_id}")

    assert invalid.status_code == 422
    assert listed.status_code == 200
    assert any(item["id"] == instrumento_id for item in listed.json()["items"])
    assert found.status_code == 200
    assert dashboard.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["status"] == "PUBLICADO"
    assert reindex.status_code == 202
    assert reindex.json()["status"] == "PENDENTE"
    assert dashboard_after_reindex.status_code == 200
    assert dashboard_after_reindex.json()["indexacao_jobs_recentes"]
    assert deleted.status_code == 200
    assert missing_delete.status_code == 404


def test_crud_campos_por_funcao():
    client = authenticated_client()
    code = unique_code()
    instrumento = client.post("/api/v1/instrumentos", json=instrumento_payload(code))
    assert instrumento.status_code == 201
    instrumento_id = instrumento.json()["id"]

    created = client.post(f"/api/v1/instrumentos/{instrumento_id}/campos", json=campo_payload(code))
    assert created.status_code == 201
    campo_id = created.json()["id"]

    invalid = client.post(f"/api/v1/instrumentos/{instrumento_id}/campos", json=campo_payload(code, chave="1_invalida"))
    duplicate = client.post(f"/api/v1/instrumentos/{instrumento_id}/campos", json=campo_payload(code))
    listed = client.get(f"/api/v1/instrumentos/{instrumento_id}/campos")
    schema = client.get(f"/api/v1/instrumentos/{instrumento_id}/schema")
    updated = client.put(f"/api/v1/instrumentos/{instrumento_id}/campos/{campo_id}", json={"nome": "Titulo atualizado"})
    deleted = client.delete(f"/api/v1/instrumentos/{instrumento_id}/campos/{campo_id}")
    missing_delete = client.delete(f"/api/v1/instrumentos/{instrumento_id}/campos/{campo_id}")

    assert invalid.status_code == 422
    assert duplicate.status_code == 409
    assert listed.status_code == 200
    assert any(item["id"] == campo_id for item in listed.json())
    assert schema.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["nome"] == "Titulo atualizado"
    assert deleted.status_code == 200
    assert missing_delete.status_code == 404

    delete_instrumento = client.delete(f"/api/v1/instrumentos/{instrumento_id}")

    assert delete_instrumento.status_code == 200
    assert registros_collection().count_documents({"instrumento_id": instrumento_id}) == 0


def test_crud_registros_dinamicos_por_funcao():
    client = authenticated_client()
    code = unique_code()
    instrumento = client.post("/api/v1/instrumentos", json=instrumento_payload(code))
    assert instrumento.status_code == 201
    instrumento_id = instrumento.json()["id"]

    campo = client.post(f"/api/v1/instrumentos/{instrumento_id}/campos", json=campo_payload(code))
    assert campo.status_code == 201
    chave = campo.json()["chave"]

    created = client.post(
        f"/api/v1/instrumentos/{instrumento_id}/registros",
        json={"dados": {chave: "Valor inicial para busca funcional"}, "status": "ATIVO"},
    )
    invalid = client.post(f"/api/v1/instrumentos/{instrumento_id}/registros", json={"dados": {}, "status": "ATIVO"})
    assert created.status_code == 201
    assert invalid.status_code == 422
    registro_id = created.json()["id"]

    listed = client.get(f"/api/v1/instrumentos/{instrumento_id}/registros")
    searched = client.post(f"/api/v1/instrumentos/{instrumento_id}/buscar", json={"q": "busca funcional", "page_size": 10})
    found = client.get(f"/api/v1/instrumentos/{instrumento_id}/registros/{registro_id}")
    updated = client.put(
        f"/api/v1/instrumentos/{instrumento_id}/registros/{registro_id}",
        json={"dados": {chave: "Valor atualizado"}, "status": "ATIVO"},
    )
    deleted = client.delete(f"/api/v1/instrumentos/{instrumento_id}/registros/{registro_id}")
    listed_after_delete = client.get(f"/api/v1/instrumentos/{instrumento_id}/registros")

    assert listed.status_code == 200
    assert searched.status_code == 200
    assert any(item["id"] == registro_id for item in searched.json()["items"])
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["dados"][chave] == "Valor atualizado"
    assert deleted.status_code == 200
    assert listed_after_delete.status_code == 200
    assert all(item["id"] != registro_id for item in listed_after_delete.json()["items"])

    delete_instrumento = client.delete(f"/api/v1/instrumentos/{instrumento_id}")

    assert delete_instrumento.status_code == 200
    assert registros_collection().count_documents({"instrumento_id": instrumento_id}) == 0
