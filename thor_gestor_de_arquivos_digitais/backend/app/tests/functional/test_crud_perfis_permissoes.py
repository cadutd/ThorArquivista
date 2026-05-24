from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error, missing_uuid


def permissao_payload(code: str, **overrides):
    payload = {
        "codigo": f"test-{code}.consultar",
        "nome": f"Consultar função {code}",
        "descricao": "Permissão criada por teste funcional.",
        "modulo": "testes",
        "funcao": f"funcao-{code}",
        "acao": "CONSULTAR",
        "ativo": True,
    }
    payload.update(overrides)
    return payload


def perfil_payload(code: str, permissao_ids: list[str] | None = None, **overrides):
    payload = {
        "codigo": f"TEST_{code}".upper(),
        "nome": f"Perfil Funcional {code}",
        "descricao": "Perfil criado por teste funcional.",
        "ativo": True,
        "sistema": False,
        "permissao_ids": permissao_ids or [],
    }
    payload.update(overrides)
    return payload


def test_permissoes_somente_leitura(client: TestClient, unique_code: str):
    listed = client.get("/api/v1/permissoes", params={"limit": 10})
    missing = client.get(f"/api/v1/permissoes/{missing_uuid()}")
    created = client.post("/api/v1/permissoes", json=permissao_payload(unique_code))
    updated = client.put(f"/api/v1/permissoes/{missing_uuid()}", json={"nome": f"Permissão Atualizada {unique_code}"})
    deleted = client.delete(f"/api/v1/permissoes/{missing_uuid()}")

    assert listed.status_code == 200
    assert "items" in listed.json()
    assert missing.status_code == 404
    assert created.status_code == 405
    assert updated.status_code == 405
    assert deleted.status_code == 405


def test_crud_perfil_com_permissoes(client: TestClient, unique_code: str):
    created = client.post("/api/v1/perfis", json=perfil_payload(unique_code))
    invalid = client.post("/api/v1/perfis", json={"codigo": "x", "nome": "", "permissao_ids": []})
    perfil_id = created.json()["id"]

    listed = client.get("/api/v1/perfis", params={"q": unique_code})
    found = client.get(f"/api/v1/perfis/{perfil_id}")
    updated = client.put(f"/api/v1/perfis/{perfil_id}", json={"nome": f"Perfil Atualizado {unique_code}", "permissao_ids": []})
    duplicated = client.post("/api/v1/perfis", json=perfil_payload(f"{unique_code}x", codigo=f"TEST_{unique_code}".upper()))
    missing_update = client.put(f"/api/v1/perfis/{missing_uuid()}", json={"nome": "Perfil inexistente"})
    deleted = client.delete(f"/api/v1/perfis/{perfil_id}")
    missing_delete = client.delete(f"/api/v1/perfis/{perfil_id}")

    assert created.status_code == 201
    assert created.json()["permissoes"] == []
    assert_validation_error(invalid)
    assert listed.status_code == 200
    assert any(item["id"] == perfil_id for item in listed.json()["items"])
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["permissoes"] == []
    assert duplicated.status_code == 409
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404
