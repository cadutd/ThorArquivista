from __future__ import annotations

from fastapi.testclient import TestClient

import app.api.v1.usuarios as usuarios_api
from app.tests.conftest import assert_validation_error, missing_uuid


def usuario_payload(code: str, **overrides):
    payload = {
        "keycloak_sub": f"sub-{code}",
        "username": f"usuario_{code}",
        "nome": f"Usuário Funcional {code}",
        "email": f"usuario_{code}@example.com",
        "papel": "OPERADOR",
        "ativo": True,
        "observacoes": "Cadastro criado por teste funcional.",
    }
    payload.update(overrides)
    return payload


def test_crud_usuario_por_funcao(client: TestClient, unique_code: str):
    created = client.post("/api/v1/usuarios", json=usuario_payload(unique_code))
    invalid = client.post(
        "/api/v1/usuarios",
        json={"username": "ab", "nome": "", "email": "email-invalido", "papel": "OPERADOR"},
    )
    usuario_id = created.json()["id"]

    listed = client.get("/api/v1/usuarios", params={"q": unique_code})
    found = client.get(f"/api/v1/usuarios/{usuario_id}")
    updated = client.put(
        f"/api/v1/usuarios/{usuario_id}",
        json={"nome": f"Usuário Atualizado {unique_code}", "papel": "ARQUIVISTA", "ativo": False},
    )
    duplicated = client.post(
        "/api/v1/usuarios",
        json=usuario_payload(f"{unique_code}x", username=f"usuario_{unique_code}"),
    )
    missing_update = client.put(
        f"/api/v1/usuarios/{missing_uuid()}",
        json={"nome": "Usuário inexistente"},
    )
    deleted = client.delete(f"/api/v1/usuarios/{usuario_id}")
    missing_delete = client.delete(f"/api/v1/usuarios/{usuario_id}")

    assert created.status_code == 201
    assert created.json()["username"] == f"usuario_{unique_code}".lower()
    assert_validation_error(invalid)
    assert listed.status_code == 200
    assert any(item["id"] == usuario_id for item in listed.json()["items"])
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["papel"] == "ARQUIVISTA"
    assert updated.json()["ativo"] is False
    assert duplicated.status_code == 409
    assert missing_update.status_code == 404
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404


def test_criar_conta_identidade_atualiza_vinculo_local(
    client: TestClient,
    unique_code: str,
    monkeypatch,
):
    async def fake_create_identity_account(usuario, provider):
        return {
            "provider": "KEYCLOAK",
            "provider_user_id": f"provider-{unique_code}",
            "temporary_password": "TempPass123!",
            "username": usuario.username,
            "email": usuario.email,
        }

    monkeypatch.setattr(usuarios_api, "create_identity_account", fake_create_identity_account)

    created = client.post("/api/v1/usuarios", json=usuario_payload(unique_code, keycloak_sub=None))
    usuario_id = created.json()["id"]
    identity = client.post(
        f"/api/v1/usuarios/{usuario_id}/identity-accounts",
        json={"provider": "KEYCLOAK"},
    )
    found = client.get(f"/api/v1/usuarios/{usuario_id}")

    assert created.status_code == 201
    assert identity.status_code == 201
    assert identity.json()["temporary_password"] == "TempPass123!"
    assert found.status_code == 200
    assert found.json()["keycloak_sub"] == f"provider-{unique_code}"

    client.delete(f"/api/v1/usuarios/{usuario_id}")
