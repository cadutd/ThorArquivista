from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.functional.test_crud_admissao import (
    alterar_status_sessao,
    create_acordo,
    create_processo,
    create_sessao,
    create_sip,
    evento_payload,
    reuniao_payload,
    sessao_payload,
    sip_payload,
)
from app.tests.functional.test_crud_unidades_acondicionamento import unidade_payload


def test_fluxo_integrado_sessao_validada_normalizada_e_finalizada(client: TestClient, unique_code: str):
    processo = create_processo(client, f"INT-SES-VAL-{unique_code}")
    acordo = create_acordo(client, processo["id"], titulo=f"Acordo sessão validada {unique_code}", status="ATIVO")
    sessao = create_sessao(
        client,
        processo["id"],
        acordo["id"],
        titulo=f"Sessão validada {unique_code}",
        responsavel_envio="Produtor integrado",
        responsavel_recebimento="Arquivo integrado",
        volume_informado="10 GB",
        caminho_origem="/origem/sessao-validada",
        observacoes="Observação integrada da sessão validada.",
    )
    sip_1 = create_sip(client, sessao["id"], f"INT-SES-VAL-1-{unique_code}")
    sip_2 = create_sip(client, sessao["id"], f"INT-SES-VAL-2-{unique_code}")

    transferencia = alterar_status_sessao(client, sessao["id"], "EM_TRANSFERENCIA")
    recebida = alterar_status_sessao(client, sessao["id"], "RECEBIDA", volume_recebido="9.8 GB")
    quarentena = alterar_status_sessao(client, sessao["id"], "EM_QUARENTENA")
    validacao = alterar_status_sessao(client, sessao["id"], "EM_VALIDACAO")
    validada = alterar_status_sessao(
        client,
        sessao["id"],
        "VALIDADA",
        resultado_validacao="SIPs íntegros e metadados conferidos.",
    )
    normalizando = alterar_status_sessao(client, sessao["id"], "NORMALIZANDO")
    normalizada = alterar_status_sessao(client, sessao["id"], "NORMALIZADA")
    finalizada = alterar_status_sessao(client, sessao["id"], "FINALIZADA")
    detalhe = client.get(f"/api/v1/admissao/sessoes/{sessao['id']}")
    sips = client.get(f"/api/v1/admissao/processos/{processo['id']}/sips")
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")

    assert sessao["status"] == "INICIADA"
    assert sessao["id_acordo_utilizado"] == acordo["id"]
    assert sip_1["id_sessao_submissao"] == sessao["id"]
    assert sip_2["id_sessao_submissao"] == sessao["id"]
    assert transferencia["status"] == "EM_TRANSFERENCIA"
    assert recebida["status"] == "RECEBIDA"
    assert recebida["volume_recebido"] == "9.8 GB"
    assert quarentena["status"] == "EM_QUARENTENA"
    assert validacao["status"] == "EM_VALIDACAO"
    assert validada["status"] == "VALIDADA"
    assert validada["resultado_validacao"] == "SIPs íntegros e metadados conferidos."
    assert normalizando["status"] == "NORMALIZANDO"
    assert normalizada["status"] == "NORMALIZADA"
    assert finalizada["status"] == "FINALIZADA"
    assert finalizada["data_fim"] is not None
    assert detalhe.status_code == 200
    assert detalhe.json()["status"] == "FINALIZADA"
    assert sips.status_code == 200
    assert {item["id"] for item in sips.json()} >= {sip_1["id"], sip_2["id"]}
    assert eventos.status_code == 200
    descricoes = [item["descricao"] for item in eventos.json()]
    tipos_evento = [item["tipo_evento"] for item in eventos.json()]
    assert {
        "SESSAO_INICIADA",
        "SESSAO_EM_TRANSFERENCIA",
        "SESSAO_RECEBIDA",
        "SESSAO_EM_QUARENTENA",
        "SESSAO_EM_VALIDACAO",
        "SESSAO_VALIDADA",
        "SESSAO_NORMALIZANDO",
        "SESSAO_NORMALIZADA",
        "SESSAO_FINALIZADA",
    }.issubset(set(tipos_evento))
    assert any("Sessão de submissão" in descricao and "iniciada" in descricao for descricao in descricoes)
    assert any("transferência iniciada" in descricao for descricao in descricoes)
    assert any("transferência finalizada" in descricao for descricao in descricoes)
    assert any("quarentena iniciada" in descricao for descricao in descricoes)
    assert any("quarentena finalizada" in descricao for descricao in descricoes)
    assert any("validação iniciada" in descricao for descricao in descricoes)
    assert any("validação concluída com aprovação" in descricao for descricao in descricoes)
    assert any("normalização iniciada" in descricao for descricao in descricoes)
    assert any("normalização finalizada" in descricao for descricao in descricoes)
    assert any("finalizada" in descricao for descricao in descricoes)


def test_fluxo_integrado_sessao_rejeitada_finaliza_sem_normalizacao(client: TestClient, unique_code: str):
    processo = create_processo(client, f"INT-SES-REJ-{unique_code}")
    acordo = create_acordo(client, processo["id"], titulo=f"Acordo sessão rejeitada {unique_code}", status="ATIVO")
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo=f"Sessão rejeitada {unique_code}")
    create_sip(client, sessao["id"], f"INT-SES-REJ-{unique_code}")

    alterar_status_sessao(client, sessao["id"], "EM_TRANSFERENCIA")
    alterar_status_sessao(client, sessao["id"], "RECEBIDA", volume_recebido="3 GB")
    alterar_status_sessao(client, sessao["id"], "EM_QUARENTENA")
    alterar_status_sessao(client, sessao["id"], "EM_VALIDACAO")
    rejeitada = alterar_status_sessao(
        client,
        sessao["id"],
        "REJEITADA",
        resultado_validacao="Falha de fixidez no SIP.",
    )
    normalizando = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "NORMALIZANDO"})
    finalizada = alterar_status_sessao(client, sessao["id"], "FINALIZADA")
    detalhe = client.get(f"/api/v1/admissao/sessoes/{sessao['id']}")
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")

    assert rejeitada["status"] == "REJEITADA"
    assert rejeitada["resultado_validacao"] == "Falha de fixidez no SIP."
    assert normalizando.status_code == 422
    assert finalizada["status"] == "FINALIZADA"
    assert detalhe.status_code == 200
    assert detalhe.json()["status"] == "FINALIZADA"
    descricoes = [item["descricao"] for item in eventos.json()]
    tipos_evento = [item["tipo_evento"] for item in eventos.json()]
    assert "SESSAO_REJEITADA" in tipos_evento
    assert "SESSAO_FINALIZADA" in tipos_evento
    assert "SESSAO_NORMALIZANDO" not in tipos_evento
    assert any("validação concluída com rejeição" in descricao for descricao in descricoes)
    assert any("finalizada" in descricao for descricao in descricoes)


def test_fluxo_integrado_admissao_ate_transformacao_sip_em_aip(client: TestClient, unique_code: str):
    processo = create_processo(client, f"INT-{unique_code}")

    reuniao = client.post(
        f"/api/v1/admissao/processos/{processo['id']}/reunioes",
        json=reuniao_payload(titulo=f"Reunião integrada {unique_code}"),
    )
    acordo = create_acordo(client, processo["id"], titulo=f"Acordo integrado {unique_code}", status="ATIVO")
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo=f"Sessão integrada {unique_code}")
    sip = create_sip(client, sessao["id"], f"INT-{unique_code}", titulo=f"SIP integrado {unique_code}")
    evento = client.post(
        f"/api/v1/admissao/processos/{processo['id']}/eventos",
        json=evento_payload(descricao=f"Evento integrado {unique_code}"),
    )
    unidade = client.post(
        "/api/v1/unidades-acondicionamento",
        json=unidade_payload(f"ADM-INT-{unique_code}", titulo=f"AIP integrado {unique_code}"),
    )
    validado = client.post(f"/api/v1/admissao/sips/{sip['id']}/validar")
    relacao = client.post(
        f"/api/v1/admissao/sips/{sip['id']}/transformar-em-aip",
        json={"id_unidade_acondicionamento": unidade.json()["id"], "tipo_relacao": "ORIGEM_TOTAL"},
    )
    processo_atualizado = client.put(
        f"/api/v1/admissao/processos/{processo['id']}",
        json={"status": "CONCLUIDO", "resultado_final": "ADMITIDO", "data_encerramento": "2026-05-19"},
    )
    detalhe = client.get(f"/api/v1/admissao/processos/{processo['id']}")
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")
    sips = client.get(f"/api/v1/admissao/processos/{processo['id']}/sips")

    assert reuniao.status_code == 201
    assert acordo["status"] == "ATIVO"
    assert sessao["id_acordo_utilizado"] == acordo["id"]
    assert sip["id_sessao_submissao"] == sessao["id"]
    assert evento.status_code == 201
    assert unidade.status_code == 201
    assert validado.status_code == 200
    assert relacao.status_code == 201
    assert relacao.json()["id_sip"] == sip["id"]
    assert relacao.json()["id_unidade_acondicionamento"] == unidade.json()["id"]
    assert processo_atualizado.status_code == 200
    assert processo_atualizado.json()["processo_ativo"] is False
    assert detalhe.status_code == 200
    assert detalhe.json()["status"] == "CONCLUIDO"
    assert eventos.status_code == 200
    assert len(eventos.json()) >= 4
    assert sips.status_code == 200
    assert sips.json()[0]["status"] == "TRANSFORMADO_EM_AIP"


def test_fluxo_integrado_admissao_rejeita_referencias_invalidas(client: TestClient, unique_code: str):
    processo = create_processo(client, f"INV-{unique_code}")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"])
    sip = create_sip(client, sessao["id"], f"INV-{unique_code}")

    processo_sem_acordo = create_processo(client, f"INV-SEM-ACO-{unique_code}")
    sessao_sem_acordo_vigente = client.post(
        f"/api/v1/admissao/processos/{processo_sem_acordo['id']}/sessoes",
        json=sessao_payload("00000000-0000-4000-8000-000000000000"),
    )
    sessao_acordo_inexistente = client.post(
        f"/api/v1/admissao/processos/{processo['id']}/sessoes",
        json=sessao_payload("00000000-0000-4000-8000-000000000000", titulo=f"Sessão inválida {unique_code}"),
    )
    sip_duplicado = client.post(f"/api/v1/admissao/sessoes/{sessao['id']}/sips", json=sip_payload(f"INV-{unique_code}"))
    relacao_unidade_inexistente = client.post(
        f"/api/v1/admissao/sips/{sip['id']}/transformar-em-aip",
        json={"id_unidade_acondicionamento": 0, "tipo_relacao": "ORIGEM_TOTAL"},
    )

    assert sessao_sem_acordo_vigente.status_code == 404
    assert sessao_acordo_inexistente.status_code == 201
    assert sessao_acordo_inexistente.json()["id_acordo_utilizado"] == acordo["id"]
    assert sip_duplicado.status_code == 422
    assert relacao_unidade_inexistente.status_code == 404
