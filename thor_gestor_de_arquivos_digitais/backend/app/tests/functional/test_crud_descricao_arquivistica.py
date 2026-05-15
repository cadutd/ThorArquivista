from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error, missing_uuid


def registro_payload(code: str, **overrides):
    payload = {
        "nivel": "1",
        "norma": "NOBRADE",
        "codigo_referencia": f"BR-TESTE-{code}",
        "titulo": f"Registro descritivo {code}",
        "data_inicial": "2020-01-01",
        "data_final": "2020-12-31",
    }
    payload.update(overrides)
    return payload


def test_crud_registro_descritivo_por_funcao(client: TestClient, unique_code: str):
    created = client.post("/api/v1/descricao-arquivistica/registros", json=registro_payload(unique_code))
    invalid = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(f"{unique_code}-ERR", nivel="9"),
    )
    date_error = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(f"{unique_code}-DATE", data_inicial="2021-01-01", data_final="2020-01-01"),
    )

    registro_id = created.json()["id"]
    listed = client.get("/api/v1/descricao-arquivistica/registros", params={"q": unique_code})
    tree = client.get("/api/v1/descricao-arquivistica/registros/arvore", params={"q": unique_code})
    found = client.get(f"/api/v1/descricao-arquivistica/registros/{registro_id}")
    updated = client.put(
        f"/api/v1/descricao-arquivistica/registros/{registro_id}",
        json={"titulo": f"Registro atualizado {unique_code}"},
    )
    missing_update = client.put(
        f"/api/v1/descricao-arquivistica/registros/{missing_uuid()}",
        json={"titulo": "Nao existe"},
    )
    deleted = client.delete(f"/api/v1/descricao-arquivistica/registros/{registro_id}")
    missing_delete = client.delete(f"/api/v1/descricao-arquivistica/registros/{registro_id}")

    assert created.status_code == 201
    assert_validation_error(invalid)
    assert_validation_error(date_error)
    assert listed.status_code == 200
    assert any(item["id"] == registro_id for item in listed.json())
    assert tree.status_code == 200
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["titulo"] == f"Registro atualizado {unique_code}"
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404


def test_registro_descritivo_duplicar_mover_e_associar_unidades(client: TestClient, unique_code: str):
    root = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(f"{unique_code}-ROOT", nivel="1"),
    )
    child = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(f"{unique_code}-CHILD", nivel="2", parent_id=root.json()["id"]),
    )
    other_root = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(f"{unique_code}-OTHER", nivel="1"),
    )
    unidade = client.post(
        "/api/v1/unidades-acondicionamento",
        json={
            "identificador": f"UA-DESC-{unique_code}",
            "titulo": f"Unidade descricao {unique_code}",
            "tipo_suporte": "DIGITAL",
            "tipo_unidade": "AIP",
            "nivel_acesso": "RESTRITO",
            "status": "ATIVA",
        },
    )
    assert root.status_code == 201
    assert child.status_code == 201
    assert other_root.status_code == 201
    assert unidade.status_code == 201

    duplicated = client.post(
        f"/api/v1/descricao-arquivistica/registros/{child.json()['id']}/duplicar",
        json={"parent_id": root.json()["id"], "codigo_referencia": f"BR-DUP-{unique_code}"},
    )
    moved = client.post(
        f"/api/v1/descricao-arquivistica/registros/{duplicated.json()['id']}/mover",
        json={"parent_id": other_root.json()["id"]},
    )
    associated = client.put(
        f"/api/v1/descricao-arquivistica/registros/{root.json()['id']}/unidades",
        json={"unidades_ids": [unidade.json()["id"]]},
    )
    missing_duplicate = client.post(
        f"/api/v1/descricao-arquivistica/registros/{missing_uuid()}/duplicar",
        json={},
    )

    assert duplicated.status_code == 201
    assert moved.status_code == 200
    assert moved.json()["parent_id"] == other_root.json()["id"]
    assert associated.status_code == 200
    assert associated.json()["unidades"][0]["id"] == unidade.json()["id"]
    assert missing_duplicate.status_code == 404

    client.delete(f"/api/v1/descricao-arquivistica/registros/{root.json()['id']}", params={"cascade": True})
    client.delete(f"/api/v1/descricao-arquivistica/registros/{other_root.json()['id']}", params={"cascade": True})
    client.delete(f"/api/v1/unidades-acondicionamento/{unidade.json()['id']}")
