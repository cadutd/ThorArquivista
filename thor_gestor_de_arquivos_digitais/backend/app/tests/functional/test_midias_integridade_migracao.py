from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.models.enums import StatusMidiaArmazenamento
from app.tests.functional.test_crud_unidades_acondicionamento import unidade_payload


def _tipo_midia_id(client: TestClient, code: str) -> str:
    payload = {
        "nome": f"Tipo teste {code}",
        "descricao": "Tipo criado por teste funcional.",
        "tempo_duracao_anos": 5,
        "periodicidade_checagem_meses": 6,
        "ativo": True,
    }
    response = client.post("/api/v1/tipos-midia-armazenamento", json=payload)
    if response.status_code == 201:
        return response.json()["id"]

    listed = client.get("/api/v1/tipos-midia-armazenamento", params={"q": payload["nome"], "limit": 1})
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert items
    return items[0]["id"]


def _criar_midia(
    client: TestClient,
    code: str,
    tipo_midia_id: str,
    *,
    nome_suffix: str,
    **overrides,
) -> dict:
    payload = {
        "nome": f"Midia teste {code} {nome_suffix}",
        "tipo_midia_id": tipo_midia_id,
        "ativo": True,
        "status": "ATIVA",
    }
    payload.update(overrides)
    response = client.post("/api/v1/midias-armazenamento", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _payload_migracao(code: str, tipo_midia_id: str, destino_suffix: str) -> dict:
    return {
        "nova_midia": {
            "nome": f"Midia destino {code} {destino_suffix}",
            "tipo_midia_id": tipo_midia_id,
            "ativo": True,
        },
        "motivo_migracao": "Renovacao preventiva da midia",
        "procedimento_utilizado": "Copia bit a bit validada",
        "software_utilizado": "Thor Test",
        "versao_software": "1.0",
        "observacoes": "Migracao criada por teste funcional.",
    }


def _ids(items: list[dict]) -> set[int]:
    return {int(item["id"]) for item in items}


def test_verificacao_integridade_resultados_atualizam_status_e_eventos(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"VR-{unique_code}")
    expected_status = {
        "SUCESSO": "ATIVA",
        "ALERTA": "COM_ALERTA",
        "FALHA": "FALHA_INTEGRIDADE",
        "INCONCLUSIVO": "ATIVA",
    }
    expected_event_result = {
        "SUCESSO": "SUCESSO",
        "ALERTA": "ALERTA",
        "FALHA": "FALHA",
        "INCONCLUSIVO": "INDETERMINADO",
    }

    for resultado, status_esperado in expected_status.items():
        midia = _criar_midia(client, f"VR-{unique_code}", tipo_id, nome_suffix=resultado)
        response = client.post(
            f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/manual",
            json={
                "resultado": resultado,
                "software_utilizado": "pytest",
                "total_aips_verificados": 3,
                "total_sucesso": 2 if resultado != "FALHA" else 1,
                "total_falha": 1 if resultado == "FALHA" else 0,
                "total_alerta": 1 if resultado == "ALERTA" else 0,
                "relatorio_json": {"aips": []},
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["resultado"] == resultado

        found = client.get(f"/api/v1/midias-armazenamento/{midia['id']}")
        assert found.status_code == 200
        assert found.json()["status"] == status_esperado
        assert found.json()["ultima_checagem_integridade"]
        assert found.json()["proxima_checagem_integridade"]

        events = client.get(f"/api/v1/midias-armazenamento/{midia['id']}/eventos")
        assert events.status_code == 200
        checagens = [event for event in events.json() if event["tipo_evento"] == "CHECAGEM_MIDIA"]
        assert checagens
        assert checagens[0]["resultado"] == expected_event_result[resultado]
        assert checagens[0]["agente"] == "functional-test-user"
        assert checagens[0]["premis_json"]["eventType"] == "CHECAGEM_MIDIA"

    vencida = _criar_midia(
        client,
        f"VR-{unique_code}",
        tipo_id,
        nome_suffix="VALIDADE",
        data_validade=(date.today() - timedelta(days=1)).isoformat(),
    )
    sucesso = client.post(
        f"/api/v1/midias-armazenamento/{vencida['id']}/verificacoes-integridade/manual",
        json={"resultado": "SUCESSO", "total_aips_verificados": 1, "total_sucesso": 1},
    )
    assert sucesso.status_code == 201
    found = client.get(f"/api/v1/midias-armazenamento/{vencida['id']}")
    assert found.status_code == 200
    assert found.json()["status"] == "EXPIRADA"


def test_painel_integridade_lista_todas_categorias(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"PI-{unique_code}")
    now = datetime.now(timezone.utc)
    expected = {
        "validade_vencida": _criar_midia(
            client,
            f"PI-{unique_code}",
            tipo_id,
            nome_suffix="validade",
            data_validade=(date.today() - timedelta(days=2)).isoformat(),
        )["id"],
        "checagem_vencida": _criar_midia(
            client,
            f"PI-{unique_code}",
            tipo_id,
            nome_suffix="checagem",
            proxima_checagem_integridade=(now - timedelta(days=1)).isoformat(),
        )["id"],
        "proximas_vencimento": _criar_midia(
            client,
            f"PI-{unique_code}",
            tipo_id,
            nome_suffix="proxima",
            data_validade=(date.today() + timedelta(days=30)).isoformat(),
        )["id"],
        "falha_ultima_checagem": _criar_midia(
            client,
            f"PI-{unique_code}",
            tipo_id,
            nome_suffix="falha",
            status="FALHA_INTEGRIDADE",
        )["id"],
        "sem_checagem": _criar_midia(client, f"PI-{unique_code}", tipo_id, nome_suffix="sem-checagem")["id"],
        "com_alerta": _criar_midia(
            client,
            f"PI-{unique_code}",
            tipo_id,
            nome_suffix="alerta",
            status="COM_ALERTA",
        )["id"],
    }

    resumo = client.get("/api/v1/midias-armazenamento/integridade/resumo")
    assert resumo.status_code == 200
    assert all(resumo.json()[categoria] >= 1 for categoria in expected)

    for categoria, midia_id in expected.items():
        response = client.get(
            "/api/v1/midias-armazenamento/integridade/itens",
            params={"categoria": categoria, "limit": 100, "offset": 0},
        )
        assert response.status_code == 200, response.text
        assert midia_id in _ids(response.json()["items"])

    invalid = client.get(
        "/api/v1/midias-armazenamento/integridade/itens",
        params={"categoria": "categoria-inexistente"},
    )
    assert invalid.status_code == 400


def test_importar_relatorio_integridade_registra_eventos_unidades(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"IR-{unique_code}")
    midia = _criar_midia(client, f"IR-{unique_code}", tipo_id, nome_suffix="origem")
    unidade = client.post(
        "/api/v1/unidades-acondicionamento",
        json=unidade_payload(f"IR-{unique_code}", titulo="Unidade para relatorio de integridade"),
    )
    assert unidade.status_code == 201

    response = client.post(
        f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/importar-relatorio",
        json={
            "ferramenta": "Thor Caixa de Ferramentas",
            "versao": "teste",
            "relatorio_json": {
                "midia_id": midia["id"],
                "resultado_midia": "FALHA",
                "falhas": [
                    {
                        "unidade_id": unidade.json()["id"],
                        "tipo_falha": "Hash divergente",
                        "resultado": "FALHA",
                    }
                ],
            },
            "observacoes": "Relatorio importado por teste.",
        },
    )
    assert response.status_code == 201, response.text
    verificacao = response.json()
    assert verificacao["resultado"] == "FALHA"
    assert verificacao["total_aips_verificados"] == 1
    assert verificacao["total_falha"] == 1

    found = client.get(f"/api/v1/midias-armazenamento/{midia['id']}")
    assert found.status_code == 200
    assert found.json()["status"] == "FALHA_INTEGRIDADE"

    detalhe = client.get(
        f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/{verificacao['id']}"
    )
    assert detalhe.status_code == 200
    assert len(detalhe.json()["eventos_unidades"]) == 1
    assert detalhe.json()["eventos_unidades"][0]["resultado"] == "FALHA"

    mismatch = client.post(
        f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/importar-relatorio",
        json={"relatorio_json": {"midia_id": midia["id"] + 999, "resultado": "SUCESSO"}},
    )
    assert mismatch.status_code == 400

    invalid = client.post(
        f"/api/v1/midias-armazenamento/{midia['id']}/verificacoes-integridade/importar-relatorio",
        json={"relatorio_json": {}},
    )
    assert invalid.status_code == 400


def test_migracao_cobre_estados_migraveis_e_bloqueados(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"ME-{unique_code}")
    allowed_statuses = {
        "ATIVA",
        "EM_VERIFICACAO",
        "COM_ALERTA",
        "FALHA_INTEGRIDADE",
        "EXPIRADA",
    }
    blocked_statuses = {
        "EM_MIGRACAO",
        "MIGRADA",
        "DESATIVADA",
        "PERDIDA",
    }

    for status in allowed_statuses:
        origem = _criar_midia(
            client,
            f"ME-{unique_code}",
            tipo_id,
            nome_suffix=f"permitida-{status}",
            status=status,
        )
        response = client.post(
            f"/api/v1/midias-armazenamento/{origem['id']}/migrar",
            json=_payload_migracao(f"ME-{unique_code}", tipo_id, f"permitida-{status}"),
        )
        assert response.status_code == 201, response.text
        migracao = response.json()
        assert migracao["status"] == "EM_EXECUCAO"
        assert migracao["midia_origem"]["status"] == "EM_MIGRACAO"
        assert migracao["midia_destino"]["status"] == "EM_MIGRACAO"

    for status in blocked_statuses:
        origem = _criar_midia(
            client,
            f"ME-{unique_code}",
            tipo_id,
            nome_suffix=f"bloqueada-{status}",
            status=status,
            ativo=status not in {"MIGRADA", "DESATIVADA", "PERDIDA"},
        )
        response = client.post(
            f"/api/v1/midias-armazenamento/{origem['id']}/migrar",
            json=_payload_migracao(f"ME-{unique_code}", tipo_id, f"bloqueada-{status}"),
        )
        assert response.status_code == 400

    assert {status.value for status in StatusMidiaArmazenamento} == allowed_statuses | blocked_statuses


def test_migracao_cobre_estados_da_maquina_de_migracao(client: TestClient, unique_code: str):
    tipo_id = _tipo_midia_id(client, f"MM-{unique_code}")

    origem_planejada = _criar_midia(client, f"MM-{unique_code}", tipo_id, nome_suffix="planejada")
    migracao_planejada = client.post(
        f"/api/v1/midias-armazenamento/{origem_planejada['id']}/migrar",
        json=_payload_migracao(f"MM-{unique_code}", tipo_id, "planejada"),
    )
    assert migracao_planejada.status_code == 201
    updated = client.put(
        f"/api/v1/migracoes-midias/{migracao_planejada.json()['id']}",
        json={"status": "PLANEJADA", "observacoes": "Retornada para planejamento."},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "PLANEJADA"

    for status in ("AGUARDANDO_VALIDACAO", "CANCELADA"):
        origem = _criar_midia(client, f"MM-{unique_code}", tipo_id, nome_suffix=status)
        created = client.post(
            f"/api/v1/midias-armazenamento/{origem['id']}/migrar",
            json=_payload_migracao(f"MM-{unique_code}", tipo_id, status),
        )
        assert created.status_code == 201
        response = client.post(
            f"/api/v1/migracoes-midias/{created.json()['id']}/concluir",
            json={"resultado": status, "observacoes": f"Resultado {status}"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == status
        assert response.json()["data_conclusao"] is None

    origem_conclusao = _criar_midia(client, f"MM-{unique_code}", tipo_id, nome_suffix="concluida")
    created = client.post(
        f"/api/v1/midias-armazenamento/{origem_conclusao['id']}/migrar",
        json=_payload_migracao(f"MM-{unique_code}", tipo_id, "concluida"),
    )
    assert created.status_code == 201
    migracao_id = created.json()["id"]

    etapa = client.post(
        f"/api/v1/migracoes-midias/{migracao_id}/etapas",
        json={"descricao": "Copia realizada", "resultado": "SUCESSO", "evidencias": {"arquivo": "log.txt"}},
    )
    assert etapa.status_code == 200
    assert len(etapa.json()["etapas"]) == 1

    relatorio = client.post(
        f"/api/v1/migracoes-midias/{migracao_id}/relatorios",
        json={"tipo": "integridade", "referencia": "relatorio-001.json"},
    )
    assert relatorio.status_code == 200
    assert len(relatorio.json()["relatorios"]) == 1

    concluida = client.post(
        f"/api/v1/migracoes-midias/{migracao_id}/concluir",
        json={
            "resultado": "CONCLUIDA",
            "observacoes": "Migracao concluida com sucesso.",
            "relatorio_integridade_origem": "origem-ok.json",
            "relatorio_integridade_destino": "destino-ok.json",
        },
    )
    assert concluida.status_code == 200
    body = concluida.json()
    assert body["status"] == "CONCLUIDA"
    assert body["data_conclusao"]
    assert body["midia_origem"]["status"] == "MIGRADA"
    assert body["midia_origem"]["ativo"] is False
    assert body["midia_destino"]["status"] == "ATIVA"
    assert body["midia_destino"]["ativo"] is True

    origem_events = client.get(f"/api/v1/midias-armazenamento/{body['midia_origem_id']}/eventos")
    destino_events = client.get(f"/api/v1/midias-armazenamento/{body['midia_destino_id']}/eventos")
    assert origem_events.status_code == 200
    assert destino_events.status_code == 200
    assert any(event["tipo_evento"] == "MIGRACAO_MIDIA" for event in origem_events.json())
    assert any(event["tipo_evento"] == "MIGRACAO_MIDIA" for event in destino_events.json())
