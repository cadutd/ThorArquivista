from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.functional.test_crud_armazenamento import create_storage_tree
from app.tests.functional.test_crud_unidades_acondicionamento import unidade_payload


def test_fluxo_integrado_unidade_midia_copia_enderecamento_movimentacao(client: TestClient, unique_code: str):
    tree = create_storage_tree(client, f"INT-{unique_code}")
    posicao = client.post(
        "/api/v1/posicoes-armazenamento",
        json={
            "id_compartimento_armazenamento": tree["compartimento_id"],
            "codigo": f"POS-INT-{unique_code}",
            "codigo_completo": f"INT-{unique_code}-POS",
            "tipo_posicao": "POSICAO_CAIXA",
            "capacidade_unidades": 2,
        },
    )
    unidade = client.post(
        "/api/v1/unidades-acondicionamento",
        json=unidade_payload(f"INT-{unique_code}", titulo="Unidade integrada"),
    )
    midia = client.post(
        "/api/v1/midias-armazenamento",
        json={"nome": f"Midia integrada {unique_code}", "tipo": "FILESYSTEM", "ativo": True},
    )
    assert posicao.status_code == 201
    assert unidade.status_code == 201
    assert midia.status_code == 201

    copia = client.post(
        f"/api/v1/unidades-acondicionamento/{unidade.json()['id']}/copias",
        json={
            "id_midia_armazenamento": midia.json()["id"],
            "uri_copia": f"file:///aips/{unique_code}",
            "funcao_copia": "PRESERVACAO",
            "status_copia": "ATIVA",
        },
    )
    assign_unidade = client.post(
        f"/api/v1/unidades-acondicionamento/{unidade.json()['id']}/atribuir-posicao",
        json={"id_posicao": posicao.json()["id"], "motivo": "Teste integrado"},
    )
    movimentacoes = client.get(
        f"/api/v1/movimentacoes-armazenamento/unidade/{unidade.json()['id']}"
    )
    localizacao = client.get(
        f"/api/v1/unidades-acondicionamento/{unidade.json()['id']}/localizacao"
    )
    ocupacao = client.get(f"/api/v1/zonas-guarda/{tree['zona_id']}/ocupacao")

    assert copia.status_code == 201
    assert assign_unidade.status_code == 200
    assert assign_unidade.json()["id_posicao_armazenamento"] == posicao.json()["id"]
    assert movimentacoes.status_code == 200
    assert len(movimentacoes.json()) >= 1
    assert localizacao.status_code == 200
    assert localizacao.json()["id"] == posicao.json()["id"]
    assert ocupacao.status_code == 200
    assert ocupacao.json()["posicoes_ocupadas"] >= 1

    delete_occupied = client.delete(f"/api/v1/posicoes-armazenamento/{posicao.json()['id']}")
    assert delete_occupied.status_code == 409
