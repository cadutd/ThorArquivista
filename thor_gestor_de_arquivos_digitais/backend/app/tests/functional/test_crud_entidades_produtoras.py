from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error, missing_uuid


def entidade_payload(code: str, **overrides):
    payload = {
        "nome": f"Secretaria Funcional {code}",
        "sigla": f"SF{code[:6]}",
        "codigo_referencia": f"EP-{code}",
        "tipo_entidade": "ORGAO_PUBLICO",
        "natureza_juridica": "Administração pública",
        "entidade_ativa": True,
        "endereco_pais": "Brasil",
    }
    payload.update(overrides)
    return payload


def test_crud_entidade_produtora_por_funcao(client: TestClient, unique_code: str):
    created = client.post(
        "/api/v1/entidades-produtoras",
        json=entidade_payload(unique_code),
    )
    invalid = client.post(
        "/api/v1/entidades-produtoras",
        json={"nome": "", "tipo_entidade": "ORGAO_PUBLICO"},
    )
    entidade_id = created.json()["id"]

    listed = client.get("/api/v1/entidades-produtoras", params={"nome": unique_code})
    found = client.get(f"/api/v1/entidades-produtoras/{entidade_id}")
    updated = client.put(
        f"/api/v1/entidades-produtoras/{entidade_id}",
        json={"sigla": f"SG{unique_code[:6]}", "entidade_ativa": False},
    )
    missing_update = client.put(
        f"/api/v1/entidades-produtoras/{missing_uuid()}",
        json={"sigla": "MISS"},
    )
    tree = client.get("/api/v1/entidades-produtoras/arvore")
    deleted = client.delete(f"/api/v1/entidades-produtoras/{entidade_id}")
    missing_delete = client.delete(f"/api/v1/entidades-produtoras/{entidade_id}")

    assert created.status_code == 201
    assert created.json()["nome_normalizado"] == f"secretaria funcional {unique_code}"
    assert_validation_error(invalid)
    assert listed.status_code == 200
    assert any(item["id"] == entidade_id for item in listed.json()["items"])
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["entidade_ativa"] is False
    assert missing_update.status_code == 404
    assert tree.status_code == 200
    assert deleted.status_code == 204
    assert missing_delete.status_code == 404


def test_entidade_produtora_hierarquia_impede_autorreferencia_e_ciclo(
    client: TestClient,
    unique_code: str,
):
    superior = client.post(
        "/api/v1/entidades-produtoras",
        json=entidade_payload(f"{unique_code}a", nome=f"Superior {unique_code}"),
    )
    assert superior.status_code == 201
    superior_id = superior.json()["id"]

    subordinada = client.post(
        "/api/v1/entidades-produtoras",
        json=entidade_payload(
            f"{unique_code}b",
            nome=f"Subordinada {unique_code}",
            id_entidade_superior=superior_id,
        ),
    )
    assert subordinada.status_code == 201
    subordinada_id = subordinada.json()["id"]

    autorreferencia = client.put(
        f"/api/v1/entidades-produtoras/{superior_id}",
        json={"id_entidade_superior": superior_id},
    )
    ciclo = client.put(
        f"/api/v1/entidades-produtoras/{superior_id}",
        json={"id_entidade_superior": subordinada_id},
    )
    tree = client.get("/api/v1/entidades-produtoras/arvore")
    children = client.get(
        "/api/v1/entidades-produtoras/arvore",
        params={"parent_id": superior_id},
    )

    assert autorreferencia.status_code == 422
    assert ciclo.status_code == 422
    assert tree.status_code == 200
    raiz = next(item for item in tree.json() if item["id"] == superior_id)
    assert raiz["has_children"] is True
    assert raiz["filhos"] == []
    assert children.status_code == 200
    assert any(filho["id"] == subordinada_id for filho in children.json())

    client.delete(f"/api/v1/entidades-produtoras/{subordinada_id}")
    client.delete(f"/api/v1/entidades-produtoras/{superior_id}")


def test_entidade_produtora_datas_e_alerta_duplicidade(
    client: TestClient,
    unique_code: str,
):
    primeira = client.post(
        "/api/v1/entidades-produtoras",
        json=entidade_payload(unique_code, nome="Órgão com Acento"),
    )
    invalida = client.post(
        "/api/v1/entidades-produtoras",
        json=entidade_payload(
            f"{unique_code}x",
            nome=f"Invalida {unique_code}",
            data_inicio="2026-05-10",
            data_fim="2026-05-01",
        ),
    )
    duplicada = client.post(
        "/api/v1/entidades-produtoras",
        json=entidade_payload(
            f"{unique_code}y",
            nome="Orgao com Acento",
            sigla=f"X{unique_code[:6]}",
            codigo_referencia=f"X-{unique_code}",
        ),
    )

    assert primeira.status_code == 201
    assert invalida.status_code == 422
    assert duplicada.status_code == 201
    assert duplicada.json()["avisos_duplicidade"]

    client.delete(f"/api/v1/entidades-produtoras/{duplicada.json()['id']}")
    client.delete(f"/api/v1/entidades-produtoras/{primeira.json()['id']}")
