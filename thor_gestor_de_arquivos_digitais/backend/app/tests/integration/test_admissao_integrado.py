from __future__ import annotations

from fastapi.testclient import TestClient

from app.tests.functional.test_crud_admissao import (
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

    sessao_acordo_inexistente = client.post(
        f"/api/v1/admissao/processos/{processo['id']}/sessoes",
        json=sessao_payload("00000000-0000-4000-8000-000000000000", titulo=f"Sessão inválida {unique_code}"),
    )
    sip_duplicado = client.post(f"/api/v1/admissao/sessoes/{sessao['id']}/sips", json=sip_payload(f"INV-{unique_code}"))
    relacao_unidade_inexistente = client.post(
        f"/api/v1/admissao/sips/{sip['id']}/transformar-em-aip",
        json={"id_unidade_acondicionamento": 0, "tipo_relacao": "ORIGEM_TOTAL"},
    )

    assert sessao_acordo_inexistente.status_code == 404
    assert sip_duplicado.status_code == 422
    assert relacao_unidade_inexistente.status_code == 404
