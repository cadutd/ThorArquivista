from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error, missing_uuid


def instrumento_payload(code: str, **overrides):
    payload = {
        "nome": f"Instrumento funcional {code}",
        "tipo": "INVENTARIO",
        "descricao": "Criado por teste funcional.",
        "status": "RASCUNHO",
        "visibilidade": "INTERNO",
        "responsavel": "Equipe QA",
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
        "filtro_avancado": False,
        "facetavel": False,
        "ordenavel": False,
    }
    payload.update(overrides)
    return payload


def test_crud_instrumento_pesquisa_por_funcao(client: TestClient, unique_code: str):
    created = client.post("/api/v1/instrumentos-pesquisa", json=instrumento_payload(unique_code))
    invalid = client.post("/api/v1/instrumentos-pesquisa", json={"nome": ""})
    instrumento_id = created.json()["id"]

    listed = client.get("/api/v1/instrumentos-pesquisa", params={"q": unique_code})
    found = client.get(f"/api/v1/instrumentos-pesquisa/{instrumento_id}")
    updated = client.put(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}",
        json={"status": "PUBLICADO"},
    )
    missing_update = client.put(
        f"/api/v1/instrumentos-pesquisa/{missing_uuid()}",
        json={"status": "PUBLICADO"},
    )
    deleted = client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}")
    missing_delete = client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}")

    assert created.status_code == 201
    assert_validation_error(invalid)
    assert listed.status_code == 200
    assert any(item["id"] == instrumento_id for item in listed.json()["items"])
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["status"] == "PUBLICADO"
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404


def test_crud_campos_instrumento_por_funcao(client: TestClient, unique_code: str):
    instrumento = client.post("/api/v1/instrumentos-pesquisa", json=instrumento_payload(unique_code))
    assert instrumento.status_code == 201
    instrumento_id = instrumento.json()["id"]

    created = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos",
        json=campo_payload(unique_code),
    )
    invalid = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos",
        json=campo_payload(unique_code, chave="1_invalida"),
    )
    duplicate = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos",
        json=campo_payload(unique_code),
    )
    campo_id = created.json()["id"]

    listed = client.get(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos")
    found = client.get(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos/{campo_id}")
    schema = client.get(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/schema")
    reordered = client.patch(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos/reordenar",
        json={"campos": [{"id": campo_id, "ordem": 2}]},
    )
    updated = client.put(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos/{campo_id}",
        json={"nome": "Titulo atualizado"},
    )
    missing_update = client.put(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos/{missing_uuid()}",
        json={"nome": "Nao existe"},
    )
    deleted = client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos/{campo_id}")
    missing_delete = client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos/{campo_id}")

    assert created.status_code == 201
    assert_validation_error(invalid)
    assert duplicate.status_code == 409
    assert listed.status_code == 200
    assert found.status_code == 200
    assert schema.status_code == 200
    assert reordered.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["nome"] == "Titulo atualizado"
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404

    client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}")


def test_crud_registros_instrumento_por_funcao(client: TestClient, unique_code: str):
    instrumento = client.post("/api/v1/instrumentos-pesquisa", json=instrumento_payload(unique_code))
    assert instrumento.status_code == 201
    instrumento_id = instrumento.json()["id"]
    campo = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/campos",
        json=campo_payload(unique_code),
    )
    assert campo.status_code == 201
    chave = campo.json()["chave"]

    created = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros",
        json={"dados": {chave: "Valor inicial"}, "status": "ATIVO"},
    )
    invalid = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros",
        json={"dados": {}, "status": "ATIVO"},
    )
    registro_id = created.json()["id"]

    listed = client.get(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros")
    searched = client.post(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/buscar",
        json={"q": "Valor", "page_size": 10},
    )
    found = client.get(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros/{registro_id}")
    updated = client.put(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros/{registro_id}",
        json={"dados": {chave: "Valor atualizado"}, "status": "ATIVO"},
    )
    missing_update = client.put(
        f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros/nao-existe",
        json={"dados": {chave: "Valor"}, "status": "ATIVO"},
    )
    deleted = client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros/{registro_id}")
    missing_delete = client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}/registros/nao-existe")

    assert created.status_code == 201
    assert invalid.status_code == 422
    assert listed.status_code == 200
    assert searched.status_code == 200
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["dados"][chave] == "Valor atualizado"
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404

    client.delete(f"/api/v1/instrumentos-pesquisa/{instrumento_id}")
