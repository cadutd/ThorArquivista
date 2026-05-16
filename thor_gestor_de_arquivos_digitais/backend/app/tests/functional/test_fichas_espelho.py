from __future__ import annotations

from fastapi.testclient import TestClient


def unidade_payload(code: str, **overrides):
    payload = {
        "identificador": f"CX-{code}",
        "titulo": f"Caixa {code}",
        "descricao": "Processos administrativos.",
        "unidade": "Arquivo Central",
        "data_limite": "2020-2024",
        "codigo_barra": f"BAR-{code}",
        "tipo_suporte": "FISICO",
        "tipo_unidade": "CAIXA",
        "nivel_acesso": "RESTRITO",
        "status": "ATIVA",
    }
    payload.update(overrides)
    return payload


def registro_payload(code: str, **overrides):
    payload = {
        "nivel": "1",
        "norma": "NOBRADE",
        "codigo_referencia": f"BR-FICHA-{code}",
        "titulo": f"Fundo {code}",
    }
    payload.update(overrides)
    return payload


def test_modelo_ficha_espelho_crud_e_geracao(client: TestClient, unique_code: str):
    modelo_payload = {
        "nome": f"Modelo ficha {unique_code}",
        "descricao": "Modelo de teste",
        "campos": [
            "logo_instituicao",
            "unidade_produtora",
            "fundo",
            "classe",
            "subclasse",
            "descricao_conteudo",
            "data_limite",
            "identificador_caixa",
            "codigo_barras",
        ],
        "tamanho_papel": "A4",
        "orientacao": "RETRATO",
        "colunas": 1,
        "largura_cm": 18.5,
        "altura_cm": 12.0,
        "ativo": True,
    }
    modelo = client.post("/api/v1/fichas-espelho/modelos", json=modelo_payload)
    assert modelo.status_code == 201

    updated = client.put(
        f"/api/v1/fichas-espelho/modelos/{modelo.json()['id']}",
        json={"descricao": "Modelo atualizado", "largura_cm": 18.0},
    )
    listed = client.get("/api/v1/fichas-espelho/modelos", params={"q": unique_code})

    fundo = client.post("/api/v1/descricao-arquivistica/registros", json=registro_payload(f"{unique_code}-FUNDO"))
    classe = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(
            f"{unique_code}-CLASSE",
            nivel="2",
            parent_id=fundo.json()["id"],
            titulo=f"Classe {unique_code}",
        ),
    )
    subclasse = client.post(
        "/api/v1/descricao-arquivistica/registros",
        json=registro_payload(
            f"{unique_code}-SUB",
            nivel="2.5",
            parent_id=classe.json()["id"],
            titulo=f"Subclasse {unique_code}",
        ),
    )
    unidade = client.post("/api/v1/unidades-acondicionamento", json=unidade_payload(unique_code))
    associated = client.put(
        f"/api/v1/descricao-arquivistica/registros/{subclasse.json()['id']}/unidades",
        json={"unidades_ids": [unidade.json()["id"]]},
    )
    generated = client.post(
        "/api/v1/fichas-espelho/gerar",
        json={"modelo_id": modelo.json()["id"], "unidade_ids": [unidade.json()["id"]]},
    )

    assert updated.status_code == 200
    assert updated.json()["largura_cm"] == 18.0
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert fundo.status_code == 201
    assert classe.status_code == 201
    assert subclasse.status_code == 201
    assert unidade.status_code == 201
    assert associated.status_code == 200
    assert generated.status_code == 200

    ficha = generated.json()["fichas"][0]
    assert ficha["identificador_caixa"] == f"CX-{unique_code}"
    assert ficha["unidade_produtora"] == "Arquivo Central"
    assert ficha["fundo"] == f"Fundo {unique_code}-FUNDO"
    assert ficha["classe"] == f"Classe {unique_code}"
    assert ficha["subclasse"] == f"Subclasse {unique_code}"
    assert ficha["codigo_barras"] == f"BAR-{unique_code}"

    client.delete(f"/api/v1/descricao-arquivistica/registros/{fundo.json()['id']}", params={"cascade": True})
    client.delete(f"/api/v1/unidades-acondicionamento/{unidade.json()['id']}")
    client.delete(f"/api/v1/fichas-espelho/modelos/{modelo.json()['id']}")
