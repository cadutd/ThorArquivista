from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.tests.functional.test_crud_armazenamento import create_storage_tree
from app.tests.functional.test_crud_unidades_acondicionamento import unidade_payload


def _tipo_midia_id(client: TestClient, code: str) -> str:
    payload = {
        "nome": f"Tipo integrado {code}",
        "descricao": "Tipo criado por teste de integracao.",
        "tempo_duracao_anos": 4,
        "periodicidade_checagem_meses": 3,
        "ativo": True,
    }
    created = client.post("/api/v1/tipos-midia-armazenamento", json=payload)
    if created.status_code == 201:
        return created.json()["id"]

    listed = client.get("/api/v1/tipos-midia-armazenamento", params={"q": payload["nome"], "limit": 1})
    assert listed.status_code == 200
    assert listed.json()["items"]
    return listed.json()["items"][0]["id"]


def _criar_midia(client: TestClient, code: str, tipo_midia_id: str, suffix: str, **overrides) -> dict:
    payload = {
        "nome": f"Midia integrada {code} {suffix}",
        "tipo_midia_id": tipo_midia_id,
        "ativo": True,
        "status": "ATIVA",
        "data_aquisicao": date.today().isoformat(),
    }
    payload.update(overrides)
    response = client.post("/api/v1/midias-armazenamento", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _payload_migracao(code: str, tipo_midia_id: str) -> dict:
    return {
        "nova_midia": {
            "nome": f"Midia integrada {code} destino",
            "tipo_midia_id": tipo_midia_id,
            "ativo": True,
            "data_aquisicao": date.today().isoformat(),
        },
        "motivo_migracao": "Substituicao preventiva apos verificacao integrada",
        "procedimento_utilizado": "Copia validada por fixidez",
        "software_utilizado": "Thor Integracao",
        "versao_software": "1.0",
        "observacoes": "Fluxo integrado de migracao.",
    }


def _criar_posicao(client: TestClient, code: str) -> int:
    tree = create_storage_tree(client, f"MID-{code}")
    posicao = client.post(
        "/api/v1/posicoes-armazenamento",
        json={
            "id_compartimento_armazenamento": tree["compartimento_id"],
            "codigo": f"POS-MID-{code}",
            "codigo_completo": f"MID-{code}-POS",
            "tipo_posicao": "SLOT_MIDIA",
            "capacidade_midias": 2,
        },
    )
    assert posicao.status_code == 201, posicao.text
    return posicao.json()["id"]


def test_fluxo_integrado_verificacao_midia_eventos_unidade_e_painel(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"VI-{unique_code}")
    midia = _criar_midia(client, f"VI-{unique_code}", tipo_id, "origem")
    unidade = client.post(
        "/api/v1/unidades-acondicionamento",
        json=unidade_payload(f"VI-{unique_code}", titulo="AIP para verificacao integrada"),
    )
    assert unidade.status_code == 201
    unidade_body = unidade.json()

    copia = client.post(
        f"/api/v1/unidades-acondicionamento/{unidade_body['id']}/copias",
        json={
            "id_midia_armazenamento": midia["id"],
            "uri_copia": f"file:///preservacao/{unidade_body['identificador']}/manifest.json",
            "funcao_copia": "PRESERVACAO",
            "status_copia": "ATIVA",
            "algoritmo_fixidez": "SHA-256",
            "hash_fixidez": "abc123",
        },
    )
    assert copia.status_code == 201

    verificacao = client.post(
        f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/importar-relatorio",
        json={
            "ferramenta": "Thor Caixa de Ferramentas",
            "versao": "integracao",
            "relatorio_json": {
                "midia_id": midia["id"],
                "resultado_midia": "ALERTA",
                "aips": [
                    {
                        "identificador": unidade_body["identificador"],
                        "resultado": "SUCESSO",
                        "detalhe": "AIP localizado e hash validado",
                    }
                ],
                "alertas": [
                    {
                        "identificador": unidade_body["identificador"],
                        "resultado": "ALERTA",
                        "mensagem": "Copia sem segunda replica",
                    }
                ],
            },
            "observacoes": "Relatorio integrado com alerta.",
        },
    )
    assert verificacao.status_code == 201, verificacao.text
    verificacao_body = verificacao.json()
    assert verificacao_body["resultado"] == "ALERTA"
    assert verificacao_body["total_aips_verificados"] == 1
    assert verificacao_body["total_alerta"] == 1

    midia_atualizada = client.get(f"/api/v1/midias-armazenamento/{midia['id']}")
    assert midia_atualizada.status_code == 200
    assert midia_atualizada.json()["status"] == "COM_ALERTA"

    detalhe = client.get(
        f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/{verificacao_body['id']}"
    )
    assert detalhe.status_code == 200
    eventos_unidades = detalhe.json()["eventos_unidades"]
    assert {evento["resultado"] for evento in eventos_unidades} == {"SUCESSO", "ALERTA"}
    assert all(evento["id_unidade_acondicionamento"] == unidade_body["id"] for evento in eventos_unidades)

    eventos_midia = client.get(f"/api/v1/midias-armazenamento/{midia['id']}/eventos")
    assert eventos_midia.status_code == 200
    checagens = [evento for evento in eventos_midia.json() if evento["tipo_evento"] == "CHECAGEM_MIDIA"]
    assert checagens
    assert checagens[0]["resultado"] == "ALERTA"
    assert checagens[0]["premis_json"]["verificationSummary"]["totalAipsVerified"] == 1

    painel = client.get(
        "/api/v1/midias-armazenamento/integridade/itens",
        params={"categoria": "com_alerta", "limit": 100, "offset": 0},
    )
    assert painel.status_code == 200
    assert midia["id"] in {item["id"] for item in painel.json()["items"]}


def test_fluxo_integrado_migracao_com_enderecamento_eventos_e_bloqueio(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"MI-{unique_code}")
    posicao_id = _criar_posicao(client, f"MI-{unique_code}")
    origem = _criar_midia(
        client,
        f"MI-{unique_code}",
        tipo_id,
        "origem",
        data_validade=(date.today() + timedelta(days=30)).isoformat(),
    )

    atribuicao = client.post(
        f"/api/v1/midias-armazenamento/{origem['id']}/atribuir-posicao",
        json={"id_posicao": posicao_id, "motivo": "Entrada em deposito para migracao"},
    )
    assert atribuicao.status_code == 200
    assert atribuicao.json()["id_posicao_armazenamento"] == posicao_id

    migracao = client.post(
        f"/api/v1/midias-armazenamento/{origem['id']}/migrar",
        json=_payload_migracao(f"MI-{unique_code}", tipo_id),
    )
    assert migracao.status_code == 201, migracao.text
    migracao_body = migracao.json()
    assert migracao_body["status"] == "EM_EXECUCAO"
    assert migracao_body["midia_origem"]["status"] == "EM_MIGRACAO"
    assert migracao_body["midia_destino"]["status"] == "EM_MIGRACAO"

    etapa = client.post(
        f"/api/v1/migracoes-midias/{migracao_body['id']}/etapas",
        json={
            "descricao": "Leitura da origem e gravacao do destino",
            "resultado": "SUCESSO",
            "evidencias": {"log": "copiado"},
        },
    )
    assert etapa.status_code == 200
    assert etapa.json()["etapas"][0]["usuario"] == "functional-test-user"

    relatorio = client.post(
        f"/api/v1/migracoes-midias/{migracao_body['id']}/relatorios",
        json={"tipo": "fixidez", "referencia": "relatorio-integrado.json", "descricao": "Hashes conferidos"},
    )
    assert relatorio.status_code == 200
    assert relatorio.json()["relatorios"][0]["usuario"] == "functional-test-user"

    conclusao = client.post(
        f"/api/v1/migracoes-midias/{migracao_body['id']}/concluir",
        json={
            "resultado": "CONCLUIDA",
            "observacoes": "Migracao integrada concluida.",
            "relatorio_integridade_origem": "origem-integrada.json",
            "relatorio_integridade_destino": "destino-integrada.json",
        },
    )
    assert conclusao.status_code == 200
    concluida = conclusao.json()
    assert concluida["status"] == "CONCLUIDA"
    assert concluida["midia_origem"]["status"] == "MIGRADA"
    assert concluida["midia_origem"]["ativo"] is False
    assert concluida["midia_destino"]["status"] == "ATIVA"
    assert concluida["midia_destino"]["ativo"] is True

    origem_events = client.get(f"/api/v1/midias-armazenamento/{concluida['midia_origem_id']}/eventos")
    destino_events = client.get(f"/api/v1/midias-armazenamento/{concluida['midia_destino_id']}/eventos")
    assert origem_events.status_code == 200
    assert destino_events.status_code == 200
    assert len([evento for evento in origem_events.json() if evento["tipo_evento"] == "MIGRACAO_MIDIA"]) >= 2
    assert len([evento for evento in destino_events.json() if evento["tipo_evento"] == "MIGRACAO_MIDIA"]) >= 2

    remigracao = client.post(
        f"/api/v1/midias-armazenamento/{concluida['midia_origem_id']}/migrar",
        json={
            **_payload_migracao(f"MI-{unique_code}", tipo_id),
            "nova_midia": {
                "nome": f"Midia integrada {unique_code} remigracao bloqueada",
                "tipo_midia_id": tipo_id,
                "ativo": True,
            },
        },
    )
    assert remigracao.status_code == 400
