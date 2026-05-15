from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error


def unidade_payload(code: str, **overrides):
    payload = {
        "identificador": f"UA-{code}",
        "titulo": f"Unidade funcional {code}",
        "descricao": "Criada por teste funcional.",
        "tipo_suporte": "DIGITAL",
        "tipo_unidade": "AIP",
        "nivel_acesso": "RESTRITO",
        "status": "ATIVA",
    }
    payload.update(overrides)
    return payload


def test_criar_unidade_sucesso(client: TestClient, unique_code: str):
    response = client.post("/api/v1/unidades-acondicionamento", json=unidade_payload(unique_code))

    assert response.status_code == 201
    data = response.json()
    assert data["identificador"] == f"UA-{unique_code}"
    assert data["titulo"] == f"Unidade funcional {unique_code}"

    client.delete(f"/api/v1/unidades-acondicionamento/{data['id']}")


def test_criar_unidade_erro_payload_invalido(client: TestClient):
    response = client.post("/api/v1/unidades-acondicionamento", json={"titulo": "Sem identificador"})

    assert_validation_error(response)


def test_criar_unidade_erro_identificador_duplicado(client: TestClient, unique_code: str):
    payload = unidade_payload(unique_code)
    created = client.post("/api/v1/unidades-acondicionamento", json=payload)
    assert created.status_code == 201

    duplicate = client.post("/api/v1/unidades-acondicionamento", json=payload)

    assert duplicate.status_code == 409

    client.delete(f"/api/v1/unidades-acondicionamento/{created.json()['id']}")


def test_listar_unidades_sucesso_com_filtro(client: TestClient, unique_code: str):
    created = client.post("/api/v1/unidades-acondicionamento", json=unidade_payload(unique_code))
    assert created.status_code == 201

    response = client.get(
        "/api/v1/unidades-acondicionamento",
        params={"q": unique_code, "limit": 10, "offset": 0},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 10
    assert any(item["identificador"] == f"UA-{unique_code}" for item in data["items"])

    client.delete(f"/api/v1/unidades-acondicionamento/{created.json()['id']}")


def test_listar_unidades_erro_paginacao_invalida(client: TestClient):
    response = client.get("/api/v1/unidades-acondicionamento", params={"limit": 0})

    assert_validation_error(response)


def test_obter_unidade_sucesso_e_erro_404(client: TestClient, unique_code: str):
    created = client.post("/api/v1/unidades-acondicionamento", json=unidade_payload(unique_code))
    assert created.status_code == 201
    unidade_id = created.json()["id"]

    found = client.get(f"/api/v1/unidades-acondicionamento/{unidade_id}")
    missing = client.get("/api/v1/unidades-acondicionamento/999999999")

    assert found.status_code == 200
    assert found.json()["id"] == unidade_id
    assert missing.status_code == 404

    client.delete(f"/api/v1/unidades-acondicionamento/{unidade_id}")


def test_atualizar_unidade_sucesso_e_erros(client: TestClient, unique_code: str):
    created = client.post("/api/v1/unidades-acondicionamento", json=unidade_payload(unique_code))
    assert created.status_code == 201
    unidade_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/unidades-acondicionamento/{unidade_id}",
        json={"titulo": f"Unidade atualizada {unique_code}"},
    )
    missing = client.patch(
        "/api/v1/unidades-acondicionamento/999999999",
        json={"titulo": "Nao existe"},
    )
    invalid = client.patch(
        f"/api/v1/unidades-acondicionamento/{unidade_id}",
        json={"tipo_suporte": "INVALIDO"},
    )

    assert updated.status_code == 200
    assert updated.json()["titulo"] == f"Unidade atualizada {unique_code}"
    assert missing.status_code == 404
    assert_validation_error(invalid)

    client.delete(f"/api/v1/unidades-acondicionamento/{unidade_id}")


def test_excluir_unidade_sucesso_e_erro_404(client: TestClient, unique_code: str):
    created = client.post("/api/v1/unidades-acondicionamento", json=unidade_payload(unique_code))
    assert created.status_code == 201
    unidade_id = created.json()["id"]

    deleted = client.delete(f"/api/v1/unidades-acondicionamento/{unidade_id}")
    missing = client.delete(f"/api/v1/unidades-acondicionamento/{unidade_id}")

    assert deleted.status_code == 204
    assert missing.status_code == 404
