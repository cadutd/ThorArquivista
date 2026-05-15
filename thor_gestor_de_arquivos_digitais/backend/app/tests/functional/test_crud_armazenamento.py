from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error


def create_storage_tree(client: TestClient, code: str):
    local = client.post(
        "/api/v1/locais-guarda",
        json={"codigo": f"LG-{code}", "nome": f"Local {code}", "tipo_local": "DEPOSITO"},
    )
    assert local.status_code == 201
    local_id = local.json()["id"]

    zona = client.post(
        "/api/v1/zonas-guarda",
        json={
            "id_local_guarda": local_id,
            "codigo": f"ZG-{code}",
            "nome": f"Zona {code}",
            "tipo_zona": "ACERVO_TEXTUAL",
        },
    )
    assert zona.status_code == 201
    zona_id = zona.json()["id"]

    estrutura = client.post(
        "/api/v1/estruturas-armazenamento",
        json={
            "id_zona_guarda": zona_id,
            "codigo": f"EST-{code}",
            "nome": f"Estrutura {code}",
            "tipo_estrutura": "ESTANTE",
        },
    )
    assert estrutura.status_code == 201
    estrutura_id = estrutura.json()["id"]

    compartimento = client.post(
        "/api/v1/compartimentos-armazenamento",
        json={
            "id_estrutura_armazenamento": estrutura_id,
            "codigo": f"COMP-{code}",
            "nome": f"Compartimento {code}",
            "tipo_compartimento": "PRATELEIRA",
        },
    )
    assert compartimento.status_code == 201
    compartimento_id = compartimento.json()["id"]

    return {
        "local_id": local_id,
        "zona_id": zona_id,
        "estrutura_id": estrutura_id,
        "compartimento_id": compartimento_id,
    }


def test_crud_local_guarda_por_funcao(client: TestClient, unique_code: str):
    payload = {"codigo": f"LG-{unique_code}", "nome": "Local inicial", "tipo_local": "DEPOSITO"}
    created = client.post("/api/v1/locais-guarda", json=payload)
    invalid = client.post("/api/v1/locais-guarda", json={"codigo": f"ERR-{unique_code}"})
    duplicate = client.post("/api/v1/locais-guarda", json=payload)
    listed = client.get("/api/v1/locais-guarda", params={"limit": 10})

    local_id = created.json()["id"]
    found = client.get(f"/api/v1/locais-guarda/{local_id}")
    updated = client.put(f"/api/v1/locais-guarda/{local_id}", json={"nome": "Local atualizado"})
    missing_update = client.put("/api/v1/locais-guarda/999999999", json={"nome": "Nao existe"})
    deleted = client.delete(f"/api/v1/locais-guarda/{local_id}")
    missing_delete = client.delete(f"/api/v1/locais-guarda/{local_id}")

    assert created.status_code == 201
    assert_validation_error(invalid)
    assert duplicate.status_code == 409
    assert listed.status_code == 200
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["nome"] == "Local atualizado"
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404


def test_crud_zona_guarda_por_funcao(client: TestClient, unique_code: str):
    local = client.post(
        "/api/v1/locais-guarda",
        json={"codigo": f"LG-{unique_code}", "nome": "Local zona", "tipo_local": "DEPOSITO"},
    )
    assert local.status_code == 201
    local_id = local.json()["id"]

    payload = {
        "id_local_guarda": local_id,
        "codigo": f"ZG-{unique_code}",
        "nome": "Zona inicial",
        "tipo_zona": "ACERVO_TEXTUAL",
    }
    created = client.post("/api/v1/zonas-guarda", json=payload)
    invalid = client.post("/api/v1/zonas-guarda", json={**payload, "id_local_guarda": 999999999})
    duplicate = client.post("/api/v1/zonas-guarda", json=payload)
    listed = client.get("/api/v1/zonas-guarda", params={"id_local_guarda": local_id})

    zona_id = created.json()["id"]
    found = client.get(f"/api/v1/zonas-guarda/{zona_id}")
    updated = client.put(f"/api/v1/zonas-guarda/{zona_id}", json={"nome": "Zona atualizada"})
    missing_update = client.put("/api/v1/zonas-guarda/999999999", json={"nome": "Nao existe"})
    deleted = client.delete(f"/api/v1/zonas-guarda/{zona_id}")
    missing_delete = client.delete("/api/v1/zonas-guarda/999999999")

    assert created.status_code == 201
    assert invalid.status_code == 404
    assert duplicate.status_code == 409
    assert listed.status_code == 200
    assert found.status_code == 200
    assert updated.status_code == 200
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404

    client.delete(f"/api/v1/locais-guarda/{local_id}")


def test_crud_estrutura_compartimento_posicao_por_funcao(client: TestClient, unique_code: str):
    tree = create_storage_tree(client, unique_code)

    estrutura = client.get(f"/api/v1/estruturas-armazenamento/{tree['estrutura_id']}")
    estrutura_update = client.put(
        f"/api/v1/estruturas-armazenamento/{tree['estrutura_id']}",
        json={"nome": "Estrutura atualizada"},
    )
    estrutura_invalid = client.post(
        "/api/v1/estruturas-armazenamento",
        json={
            "id_zona_guarda": 999999999,
            "codigo": f"ERR-EST-{unique_code}",
            "nome": "Erro",
            "tipo_estrutura": "ESTANTE",
        },
    )

    compartimento = client.get(f"/api/v1/compartimentos-armazenamento/{tree['compartimento_id']}")
    compartimento_update = client.put(
        f"/api/v1/compartimentos-armazenamento/{tree['compartimento_id']}",
        json={"nome": "Compartimento atualizado"},
    )
    compartimento_invalid = client.post(
        "/api/v1/compartimentos-armazenamento",
        json={
            "id_estrutura_armazenamento": 999999999,
            "codigo": f"ERR-COMP-{unique_code}",
            "nome": "Erro",
            "tipo_compartimento": "PRATELEIRA",
        },
    )

    posicao_payload = {
        "id_compartimento_armazenamento": tree["compartimento_id"],
        "codigo": f"POS-{unique_code}",
        "codigo_completo": f"LG-ZG-EST-COMP-POS-{unique_code}",
        "tipo_posicao": "POSICAO_CAIXA",
    }
    posicao = client.post("/api/v1/posicoes-armazenamento", json=posicao_payload)
    posicao_duplicate = client.post("/api/v1/posicoes-armazenamento", json=posicao_payload)
    posicao_id = posicao.json()["id"]
    posicao_found = client.get(f"/api/v1/posicoes-armazenamento/{posicao_id}")
    posicao_update = client.put(f"/api/v1/posicoes-armazenamento/{posicao_id}", json={"observacoes": "OK"})
    posicao_delete = client.delete(f"/api/v1/posicoes-armazenamento/{posicao_id}")
    posicao_missing = client.delete("/api/v1/posicoes-armazenamento/999999999")

    assert estrutura.status_code == 200
    assert estrutura_update.status_code == 200
    assert estrutura_invalid.status_code == 404
    assert compartimento.status_code == 200
    assert compartimento_update.status_code == 200
    assert compartimento_invalid.status_code == 404
    assert posicao.status_code == 201
    assert posicao_duplicate.status_code == 409
    assert posicao_found.status_code == 200
    assert posicao_update.status_code == 200
    assert posicao_delete.status_code == 204
    assert posicao_missing.status_code == 404

    assert client.delete(f"/api/v1/compartimentos-armazenamento/{tree['compartimento_id']}").status_code == 204
    assert client.delete(f"/api/v1/estruturas-armazenamento/{tree['estrutura_id']}").status_code == 204
    assert client.delete(f"/api/v1/zonas-guarda/{tree['zona_id']}").status_code == 204
    client.delete(f"/api/v1/locais-guarda/{tree['local_id']}")
