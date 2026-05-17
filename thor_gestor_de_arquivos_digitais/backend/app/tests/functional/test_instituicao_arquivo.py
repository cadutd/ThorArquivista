from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error


def instituicao_payload(code: str, **overrides):
    payload = {
        "nome": f"Arquivo Central Funcional {code}",
        "sigla": f"AC{code[:6]}",
        "codigo_referencia": f"BR-THOR-{code}",
        "natureza_juridica": "Órgão público",
        "esfera_administrativa": "ESTADUAL",
        "cnpj": "11.222.333/0001-81",
        "email": "arquivo.teste@thor.local",
        "telefone": "(11) 3000-0000",
        "site": "https://arquivo.example.local",
        "endereco_logradouro": "Rua da Custódia",
        "endereco_numero": "100",
        "endereco_municipio": "São Paulo",
        "endereco_uf": "SP",
        "endereco_cep": "01000-000",
        "endereco_pais": "Brasil",
        "responsavel_nome": "Responsável Funcional",
        "responsavel_cargo": "Direção",
        "responsavel_email": "responsavel@thor.local",
        "responsavel_telefone": "(11) 3000-0001",
        "historico": "Instituição criada por teste funcional.",
        "missao": "Preservar e dar acesso aos documentos digitais.",
    }
    payload.update(overrides)
    return payload


def ensure_empty(client: TestClient):
    existing = client.get("/api/v1/admin/instituicao-arquivo")
    assert existing.status_code == 200
    if existing.json():
        deleted = client.delete("/api/v1/admin/instituicao-arquivo")
        assert deleted.status_code in {204, 404}


def test_instituicao_arquivo_singleton_crud(client: TestClient, unique_code: str):
    ensure_empty(client)

    empty = client.get("/api/v1/admin/instituicao-arquivo")
    created = client.post(
        "/api/v1/admin/instituicao-arquivo",
        json=instituicao_payload(unique_code),
    )
    duplicate = client.post(
        "/api/v1/admin/instituicao-arquivo",
        json=instituicao_payload(f"{unique_code}dup", nome="Outra instituição"),
    )
    found = client.get("/api/v1/admin/instituicao-arquivo")
    updated = client.put(
        "/api/v1/admin/instituicao-arquivo",
        json={"nome": f"Arquivo Atualizado {unique_code}", "esfera_administrativa": "FEDERAL"},
    )
    invalid = client.put(
        "/api/v1/admin/instituicao-arquivo",
        json={"email": "email-invalido"},
    )
    deleted = client.delete("/api/v1/admin/instituicao-arquivo")
    missing_delete = client.delete("/api/v1/admin/instituicao-arquivo")

    assert empty.status_code == 200
    assert empty.json() is None
    assert created.status_code == 201
    assert created.json()["nome"] == f"Arquivo Central Funcional {unique_code}"
    assert duplicate.status_code == 409
    assert found.status_code == 200
    assert found.json()["id"] == created.json()["id"]
    assert updated.status_code == 200
    assert updated.json()["nome"] == f"Arquivo Atualizado {unique_code}"
    assert updated.json()["esfera_administrativa"] == "FEDERAL"
    assert_validation_error(invalid)
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404


def test_instituicao_arquivo_validacoes_backend(client: TestClient, unique_code: str):
    ensure_empty(client)

    sem_nome = client.post("/api/v1/admin/instituicao-arquivo", json={"nome": ""})
    email_invalido = client.post(
        "/api/v1/admin/instituicao-arquivo",
        json=instituicao_payload(unique_code, email="invalido@"),
    )
    responsavel_invalido = client.post(
        "/api/v1/admin/instituicao-arquivo",
        json=instituicao_payload(unique_code, responsavel_email="responsavel-invalido"),
    )
    cnpj_invalido = client.post(
        "/api/v1/admin/instituicao-arquivo",
        json=instituicao_payload(unique_code, cnpj="11.111.111/1111-11"),
    )

    assert_validation_error(sem_nome)
    assert_validation_error(email_invalido)
    assert_validation_error(responsavel_invalido)
    assert_validation_error(cnpj_invalido)
