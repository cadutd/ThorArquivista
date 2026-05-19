from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.tests.conftest import assert_validation_error, missing_uuid
from app.tests.functional.test_crud_descricao_arquivistica import registro_payload
from app.tests.functional.test_crud_entidades_produtoras import entidade_payload
from app.tests.functional.test_instituicao_arquivo import instituicao_payload


def ensure_instituicao(client: TestClient, code: str) -> dict:
    existing = client.get("/api/v1/admin/instituicao-arquivo")
    assert existing.status_code == 200
    if existing.json():
        return existing.json()
    created = client.post("/api/v1/admin/instituicao-arquivo", json=instituicao_payload(code))
    assert created.status_code == 201
    return created.json()


def create_entidade(client: TestClient, code: str) -> dict:
    created = client.post("/api/v1/entidades-produtoras", json=entidade_payload(code))
    assert created.status_code == 201
    return created.json()


def create_descricao(client: TestClient, code: str) -> dict:
    created = client.post("/api/v1/descricao-arquivistica/registros", json=registro_payload(code))
    assert created.status_code == 201
    return created.json()


def processo_payload(client: TestClient, code: str, **overrides) -> dict:
    instituicao = ensure_instituicao(client, f"ADM-{code}")
    entidade = create_entidade(client, f"ADM-{code}")
    descricao = create_descricao(client, f"ADM-{code}")
    payload = {
        "numero_processo": f"ADM-{code}",
        "titulo": f"Processo de admissão {code}",
        "descricao": "Processo criado por teste funcional.",
        "id_instituicao_arquivo": instituicao["id"],
        "id_entidade_produtora": entidade["id"],
        "id_descricao_arquivistica": descricao["id"],
        "nome_usuario_responsavel": f"Responsável {code}",
        "tipo_processo_admissao": "FECHADO",
        "tipo_ingresso": "TRANSFERENCIA",
        "tipo_suporte": "DIGITAL",
        "data_inicio": "2026-05-18",
        "processo_ativo": True,
        "admissoes_recorrentes": False,
        "status": "ABERTO",
    }
    payload.update(overrides)
    return payload


def create_processo(client: TestClient, code: str, **overrides) -> dict:
    created = client.post("/api/v1/admissao/processos", json=processo_payload(client, code, **overrides))
    assert created.status_code == 201
    return created.json()


def acordo_payload(**overrides) -> dict:
    payload = {
        "titulo": "Acordo de submissão",
        "descricao": "Descrição do acordo de admissão.",
        "status": "ATIVO",
        "data_inicio_vigencia": "2026-05-18",
        "data_fim_vigencia": "2026-12-31",
        "motivo_revisao": "Motivo de revisão registrado em teste.",
        "regras_empacotamento": "Pacotes SIP em ZIP.",
        "regras_nomenclatura": "Arquivos nomeados com código do processo.",
        "formatos_aceitos": "PDF/A, TIFF e CSV.",
        "metadados_obrigatorios": "Título, data e produtor.",
        "requisitos_fixidez": "SHA-256 obrigatório.",
        "requisitos_representacao": "Representação de preservação e acesso quando aplicável.",
        "politica_validacao": "Validar manifesto, formatos e fixidez.",
        "politica_rejeicao": "Rejeitar pacotes sem manifesto.",
        "politica_normalizacao": "Normalizar formatos proprietários quando possível.",
        "politica_sigilo": "Aplicar restrições informadas pelo produtor.",
        "periodicidade_submissao": "Mensal",
        "observacoes": "Observação de teste do acordo.",
    }
    payload.update(overrides)
    return payload


def create_acordo(client: TestClient, processo_id: str, **overrides) -> dict:
    created = client.post(f"/api/v1/admissao/processos/{processo_id}/acordos", json=acordo_payload(**overrides))
    assert created.status_code == 201
    return created.json()


def sessao_payload(acordo_id: str, **overrides) -> dict:
    payload = {
        "id_acordo_utilizado": acordo_id,
        "titulo": "Sessão de submissão",
        "data_inicio": "2026-05-18T09:00:00Z",
        "canal_submissao": "UPLOAD",
        "tipo_suporte": "DIGITAL",
        "responsavel_envio": "Produtor",
    }
    payload.update(overrides)
    return payload


def create_sessao(client: TestClient, processo_id: str, acordo_id: str, **overrides) -> dict:
    created = client.post(
        f"/api/v1/admissao/processos/{processo_id}/sessoes",
        json=sessao_payload(acordo_id, **overrides),
    )
    assert created.status_code == 201
    return created.json()


def sip_payload(code: str, **overrides) -> dict:
    payload = {
        "codigo_sip": f"SIP-{code}",
        "titulo": f"SIP {code}",
        "tipo_sip": "DIGITAL",
        "data_recebimento": "2026-05-18T10:00:00Z",
        "hash_global": f"hash-{code}",
    }
    payload.update(overrides)
    return payload


def create_sip(client: TestClient, sessao_id: str, code: str, **overrides) -> dict:
    created = client.post(f"/api/v1/admissao/sessoes/{sessao_id}/sips", json=sip_payload(code, **overrides))
    assert created.status_code == 201
    return created.json()


def alterar_status_sessao(client: TestClient, sessao_id: str, status: str, **payload) -> dict:
    response = client.patch(
        f"/api/v1/admissao/sessoes/{sessao_id}/status",
        json={"status": status, **payload},
    )
    assert response.status_code == 200
    return response.json()


def avancar_sessao_ate_estado(client: TestClient, sessao_id: str, status_destino: str) -> dict:
    passos = [
        ("EM_TRANSFERENCIA", {}),
        ("RECEBIDA", {"volume_recebido": "12 GB"}),
        ("EM_QUARENTENA", {}),
        ("EM_VALIDACAO", {}),
        ("VALIDADA", {"resultado_validacao": "Pacote validado."}),
        ("NORMALIZANDO", {}),
        ("NORMALIZADA", {}),
        ("FINALIZADA", {}),
    ]
    estado = None
    for status, payload in passos:
        estado = alterar_status_sessao(client, sessao_id, status, **payload)
        if status == status_destino:
            return estado
    raise AssertionError(f"Estado não alcançado no helper: {status_destino}")


def listar_eventos_sessao(client: TestClient, processo_id: str, sessao_id: str) -> list[dict]:
    response = client.get(f"/api/v1/admissao/processos/{processo_id}/eventos")
    assert response.status_code == 200
    return [item for item in response.json() if item["id_sessao_submissao"] == sessao_id]


def reuniao_payload(**overrides) -> dict:
    payload = {
        "titulo": "Reunião de admissão",
        "tipo_reuniao": "NEGOCIACAO_INICIAL",
        "data_reuniao": "2026-05-18T11:00:00Z",
        "participantes": "Arquivo; Produtor",
    }
    payload.update(overrides)
    return payload


def evento_payload(**overrides) -> dict:
    payload = {
        "tipo_evento": "APROVACAO",
        "descricao": "Evento manual de teste.",
        "resultado": "INFORMATIVO",
        "data_evento": "2026-05-18T12:00:00Z",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "field",
    [
        "numero_processo",
        "titulo",
        "id_instituicao_arquivo",
        "id_entidade_produtora",
        "tipo_processo_admissao",
        "tipo_ingresso",
        "tipo_suporte",
        "data_inicio",
    ],
)
def test_processo_admissao_campos_obrigatorios(client: TestClient, unique_code: str, field: str):
    payload = processo_payload(client, f"{unique_code}-{field[:3]}")
    payload.pop(field)
    response = client.post("/api/v1/admissao/processos", json=payload)
    assert_validation_error(response)


@pytest.mark.parametrize("field", ["titulo", "tipo_reuniao", "data_reuniao"])
def test_reuniao_admissao_campos_obrigatorios(client: TestClient, unique_code: str, field: str):
    processo = create_processo(client, f"{unique_code}-reu-{field[:3]}")
    payload = reuniao_payload()
    payload.pop(field)
    response = client.post(f"/api/v1/admissao/processos/{processo['id']}/reunioes", json=payload)
    assert_validation_error(response)


def test_acordo_admissao_campo_titulo_obrigatorio(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-aco")
    payload = acordo_payload()
    payload.pop("titulo")
    response = client.post(f"/api/v1/admissao/processos/{processo['id']}/acordos", json=payload)
    assert_validation_error(response)


def test_acordo_admissao_status_deve_respeitar_dominio(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-dom")
    response = client.post(
        f"/api/v1/admissao/processos/{processo['id']}/acordos",
        json=acordo_payload(status="PUBLICADO"),
    )
    assert_validation_error(response)


def test_nova_versao_acordo_copia_acordo_ativo(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-copy")
    versao_antiga = create_acordo(
        client,
        processo["id"],
        titulo="Acordo antigo",
        politica_sigilo="Sigilo antigo.",
    )
    acordo_ativo = create_acordo(
        client,
        processo["id"],
        titulo="Acordo ativo para copiar",
        politica_sigilo="Sigilo copiado do ativo.",
        regras_empacotamento="Empacotamento copiado do ativo.",
    )

    nova_versao = client.post(f"/api/v1/admissao/acordos/{versao_antiga['id']}/nova-versao")

    assert nova_versao.status_code == 201
    assert nova_versao.json()["titulo"] == acordo_ativo["titulo"]
    assert nova_versao.json()["politica_sigilo"] == "Sigilo copiado do ativo."
    assert nova_versao.json()["regras_empacotamento"] == "Empacotamento copiado do ativo."
    assert nova_versao.json()["status"] == "ATIVO"


@pytest.mark.parametrize("field", ["titulo", "data_inicio", "canal_submissao", "tipo_suporte"])
def test_sessao_submissao_campos_obrigatorios(client: TestClient, unique_code: str, field: str):
    processo = create_processo(client, f"{unique_code}-ses-{field[:3]}")
    acordo = create_acordo(client, processo["id"])
    payload = sessao_payload(acordo["id"])
    payload.pop(field)
    response = client.post(f"/api/v1/admissao/processos/{processo['id']}/sessoes", json=payload)
    assert_validation_error(response)


@pytest.mark.parametrize("field", ["codigo_sip", "titulo", "tipo_sip", "data_recebimento"])
def test_sip_admissao_campos_obrigatorios(client: TestClient, unique_code: str, field: str):
    processo = create_processo(client, f"{unique_code}-sip-{field[:3]}")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"])
    payload = sip_payload(f"{unique_code}-{field[:3]}")
    payload.pop(field)
    response = client.post(f"/api/v1/admissao/sessoes/{sessao['id']}/sips", json=payload)
    assert_validation_error(response)


@pytest.mark.parametrize("field", ["tipo_evento", "descricao"])
def test_evento_admissao_campos_obrigatorios(client: TestClient, unique_code: str, field: str):
    processo = create_processo(client, f"{unique_code}-eve-{field[:3]}")
    payload = evento_payload()
    payload.pop(field)
    response = client.post(f"/api/v1/admissao/processos/{processo['id']}/eventos", json=payload)
    assert_validation_error(response)


def test_relacao_sip_aip_campo_unidade_obrigatorio(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-rel")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"])
    sip = create_sip(client, sessao["id"], f"{unique_code}-rel")
    response = client.post(f"/api/v1/admissao/sips/{sip['id']}/transformar-em-aip", json={})
    assert_validation_error(response)


def test_crud_processo_admissao_por_funcao(client: TestClient, unique_code: str):
    created = client.post("/api/v1/admissao/processos", json=processo_payload(client, unique_code))
    duplicate = client.post("/api/v1/admissao/processos", json=processo_payload(client, f"{unique_code}-dup", numero_processo=f"ADM-{unique_code}"))
    processo_id = created.json()["id"]
    listed = client.get("/api/v1/admissao/processos", params={"q": unique_code})
    found = client.get(f"/api/v1/admissao/processos/{processo_id}")
    updated = client.put(
        f"/api/v1/admissao/processos/{processo_id}",
        json={"titulo": f"Processo atualizado {unique_code}", "status": "EM_NEGOCIACAO"},
    )
    missing_update = client.put(f"/api/v1/admissao/processos/{missing_uuid()}", json={"titulo": "Nao existe"})
    deleted = client.delete(f"/api/v1/admissao/processos/{processo_id}")

    assert created.status_code == 201
    assert created.json()["criado_por"] == "functional-test-user"
    assert created.json()["atualizado_por"] == "functional-test-user"
    assert duplicate.status_code == 422
    assert listed.status_code == 200
    assert any(item["id"] == processo_id for item in listed.json()["items"])
    assert found.status_code == 200
    assert updated.status_code == 200
    assert updated.json()["titulo"] == f"Processo atualizado {unique_code}"
    assert updated.json()["atualizado_por"] == "functional-test-user"
    assert missing_update.status_code == 404
    assert deleted.status_code == 204


def test_crud_entidades_filhas_admissao_por_funcao(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-filhas")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"])
    sip = create_sip(client, sessao["id"], f"{unique_code}-filhas")

    reuniao = client.post(f"/api/v1/admissao/processos/{processo['id']}/reunioes", json=reuniao_payload())
    evento = client.post(f"/api/v1/admissao/processos/{processo['id']}/eventos", json=evento_payload())
    reunioes = client.get(f"/api/v1/admissao/processos/{processo['id']}/reunioes")
    reuniao_atualizada = client.put(
        f"/api/v1/admissao/reunioes/{reuniao.json()['id']}",
        json={"tipo_reuniao": "ALINHAMENTO_TECNICO", "pendencias": "Pendência registrada."},
    )
    acordos = client.get(f"/api/v1/admissao/processos/{processo['id']}/acordos")
    sessoes = client.get(f"/api/v1/admissao/processos/{processo['id']}/sessoes")
    sips = client.get(f"/api/v1/admissao/processos/{processo['id']}/sips")
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")
    ativado = client.post(f"/api/v1/admissao/acordos/{acordo['id']}/ativar")
    atualizado_acordo = client.put(
        f"/api/v1/admissao/acordos/{acordo['id']}",
        json={"politica_sigilo": "Sigilo atualizado.", "status": "ATIVO"},
    )
    nova_versao = client.post(f"/api/v1/admissao/acordos/{acordo['id']}/nova-versao")
    reativar_versao_antiga = client.post(f"/api/v1/admissao/acordos/{acordo['id']}/ativar")
    validado = client.post(f"/api/v1/admissao/sips/{sip['id']}/validar")
    missing_reuniao = client.get(f"/api/v1/admissao/reunioes/{missing_uuid()}")
    reuniao_excluida = client.delete(f"/api/v1/admissao/reunioes/{reuniao.json()['id']}")
    reuniao_excluida_novamente = client.delete(f"/api/v1/admissao/reunioes/{reuniao.json()['id']}")

    assert reuniao.status_code == 201
    assert evento.status_code == 201
    assert reunioes.status_code == 200
    assert reuniao_atualizada.status_code == 200
    assert reuniao_atualizada.json()["tipo_reuniao"] == "ALINHAMENTO_TECNICO"
    assert acordos.status_code == 200
    assert sessoes.status_code == 200
    assert any(item["id"] == sessao["id"] for item in sessoes.json()["items"])
    assert sips.status_code == 200
    assert eventos.status_code == 200
    assert ativado.status_code == 200
    assert atualizado_acordo.status_code == 200
    assert atualizado_acordo.json()["politica_sigilo"] == "Sigilo atualizado."
    assert atualizado_acordo.json()["atualizado_por"] == "functional-test-user"
    assert nova_versao.status_code == 201
    assert nova_versao.json()["numero_versao"] == acordo["numero_versao"] + 1
    assert nova_versao.json()["status"] == "ATIVO"
    assert nova_versao.json()["criado_por"] == "functional-test-user"
    assert reativar_versao_antiga.status_code == 422
    assert validado.status_code == 200
    assert missing_reuniao.status_code == 404
    assert reuniao_excluida.status_code == 204
    assert reuniao_excluida_novamente.status_code == 404


def test_sessoes_submissao_paginacao_status_e_acordo_vigente(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-ses-page")
    acordo = create_acordo(client, processo["id"], titulo="Acordo vigente")
    primeira = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão 1")
    segunda = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão 2")

    page = client.get(f"/api/v1/admissao/processos/{processo['id']}/sessoes", params={"limit": 1, "offset": 0})
    status_update = client.patch(f"/api/v1/admissao/sessoes/{primeira['id']}/status", json={"status": "EM_TRANSFERENCIA"})
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")

    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert page.json()["limit"] == 1
    assert len(page.json()["items"]) == 1
    assert page.json()["items"][0]["id"] == segunda["id"]
    assert primeira["id_acordo_utilizado"] == acordo["id"]
    assert status_update.status_code == 200
    assert status_update.json()["status"] == "EM_TRANSFERENCIA"
    assert any("transferência iniciada" in item["descricao"] for item in eventos.json())


def test_sessao_submissao_exige_processo_ativo_e_acordo_vigente(client: TestClient, unique_code: str):
    processo_sem_acordo = create_processo(client, f"{unique_code}-sem-aco")
    sem_acordo = client.post(
        f"/api/v1/admissao/processos/{processo_sem_acordo['id']}/sessoes",
        json=sessao_payload("00000000-0000-4000-8000-000000000000", id_acordo_utilizado=None),
    )

    processo_cancelado = create_processo(client, f"{unique_code}-cancel")
    acordo = create_acordo(client, processo_cancelado["id"])
    client.delete(f"/api/v1/admissao/processos/{processo_cancelado['id']}")
    inativo = client.post(
        f"/api/v1/admissao/processos/{processo_cancelado['id']}/sessoes",
        json=sessao_payload(acordo["id"]),
    )

    assert sem_acordo.status_code == 404
    assert inativo.status_code == 422


def test_sessao_submissao_criacao_registra_evento_inicial(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-ses-evt-create")
    acordo = create_acordo(client, processo["id"], titulo="Acordo vigente")
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão com evento inicial")

    eventos = listar_eventos_sessao(client, processo["id"], sessao["id"])
    eventos_iniciais = [item for item in eventos if item["tipo_evento"] == "SESSAO_INICIADA"]

    assert len(eventos_iniciais) == 1
    evento = eventos_iniciais[0]
    assert evento["id_processo_admissao"] == processo["id"]
    assert evento["id_sessao_submissao"] == sessao["id"]
    assert evento["id_sip"] is None
    assert evento["id_unidade_acondicionamento"] is None
    assert evento["resultado"] == "SUCESSO"
    assert evento["agente"] == "functional-test-user"
    assert evento["criado_por"] == "functional-test-user"
    assert f"Sessão de submissão {sessao['numero_sessao']} iniciada" in evento["descricao"]


def test_sessao_submissao_cria_eventos_para_cada_estado_do_fluxo_validado(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-ses-evt-valid")
    acordo = create_acordo(client, processo["id"], titulo="Acordo vigente")
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão validada com eventos")

    alterar_status_sessao(client, sessao["id"], "EM_TRANSFERENCIA", atualizado_por="operador-eventos")
    alterar_status_sessao(client, sessao["id"], "RECEBIDA", atualizado_por="operador-eventos", volume_recebido="11 GB")
    alterar_status_sessao(client, sessao["id"], "EM_QUARENTENA", atualizado_por="operador-eventos")
    alterar_status_sessao(client, sessao["id"], "EM_VALIDACAO", atualizado_por="operador-eventos")
    alterar_status_sessao(
        client,
        sessao["id"],
        "VALIDADA",
        atualizado_por="operador-eventos",
        resultado_validacao="Validação aprovada.",
    )
    alterar_status_sessao(client, sessao["id"], "NORMALIZANDO", atualizado_por="operador-eventos")
    alterar_status_sessao(client, sessao["id"], "NORMALIZADA", atualizado_por="operador-eventos")
    alterar_status_sessao(client, sessao["id"], "FINALIZADA", atualizado_por="operador-eventos")

    eventos = listar_eventos_sessao(client, processo["id"], sessao["id"])
    tipos_evento = [item["tipo_evento"] for item in eventos]

    assert len(eventos) == 10
    assert tipos_evento.count("SESSAO_INICIADA") == 1
    assert tipos_evento.count("SESSAO_EM_TRANSFERENCIA") == 1
    assert tipos_evento.count("SESSAO_RECEBIDA") == 1
    assert tipos_evento.count("SESSAO_EM_QUARENTENA") == 1
    assert tipos_evento.count("SESSAO_EM_VALIDACAO") == 2
    assert tipos_evento.count("SESSAO_VALIDADA") == 1
    assert tipos_evento.count("SESSAO_NORMALIZANDO") == 1
    assert tipos_evento.count("SESSAO_NORMALIZADA") == 1
    assert tipos_evento.count("SESSAO_FINALIZADA") == 1
    assert all(item["id_processo_admissao"] == processo["id"] for item in eventos)
    assert all(item["id_sessao_submissao"] == sessao["id"] for item in eventos)
    assert all(item["resultado"] == "SUCESSO" for item in eventos)
    assert all(item["agente"] == "operador-eventos" for item in eventos if item["tipo_evento"] != "SESSAO_INICIADA")
    assert any("transferência iniciada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_EM_TRANSFERENCIA")
    assert any("transferência finalizada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_RECEBIDA")
    assert any("quarentena iniciada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_EM_QUARENTENA")
    assert any("validação iniciada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_EM_VALIDACAO")
    assert any("validação concluída com aprovação" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_VALIDADA")
    assert any("normalização iniciada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_NORMALIZANDO")
    assert any("normalização finalizada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_NORMALIZADA")
    assert any("finalizada" in item["descricao"] for item in eventos if item["tipo_evento"] == "SESSAO_FINALIZADA")


def test_sessao_submissao_cria_eventos_para_rejeicao_e_cancelamento(client: TestClient, unique_code: str):
    processo_rejeicao = create_processo(client, f"{unique_code}-ses-evt-rej")
    acordo_rejeicao = create_acordo(client, processo_rejeicao["id"])
    sessao_rejeicao = create_sessao(client, processo_rejeicao["id"], acordo_rejeicao["id"], titulo="Sessão rejeitada com eventos")

    alterar_status_sessao(client, sessao_rejeicao["id"], "EM_TRANSFERENCIA")
    alterar_status_sessao(client, sessao_rejeicao["id"], "RECEBIDA", volume_recebido="5 GB")
    alterar_status_sessao(client, sessao_rejeicao["id"], "EM_QUARENTENA")
    alterar_status_sessao(client, sessao_rejeicao["id"], "EM_VALIDACAO")
    alterar_status_sessao(client, sessao_rejeicao["id"], "REJEITADA", resultado_validacao="Falha de validação.")
    alterar_status_sessao(client, sessao_rejeicao["id"], "FINALIZADA")

    eventos_rejeicao = listar_eventos_sessao(client, processo_rejeicao["id"], sessao_rejeicao["id"])
    tipos_rejeicao = [item["tipo_evento"] for item in eventos_rejeicao]
    evento_rejeitada = next(item for item in eventos_rejeicao if item["tipo_evento"] == "SESSAO_REJEITADA")

    assert "SESSAO_REJEITADA" in tipos_rejeicao
    assert "SESSAO_FINALIZADA" in tipos_rejeicao
    assert "SESSAO_VALIDADA" not in tipos_rejeicao
    assert "SESSAO_NORMALIZANDO" not in tipos_rejeicao
    assert evento_rejeitada["resultado"] == "SUCESSO"
    assert "validação concluída com rejeição" in evento_rejeitada["descricao"]

    processo_cancelamento = create_processo(client, f"{unique_code}-ses-evt-can")
    acordo_cancelamento = create_acordo(client, processo_cancelamento["id"])
    sessao_cancelamento = create_sessao(client, processo_cancelamento["id"], acordo_cancelamento["id"], titulo="Sessão cancelada com eventos")

    cancelada = alterar_status_sessao(client, sessao_cancelamento["id"], "CANCELADA")
    eventos_cancelamento = listar_eventos_sessao(client, processo_cancelamento["id"], sessao_cancelamento["id"])
    evento_cancelada = next(item for item in eventos_cancelamento if item["tipo_evento"] == "SESSAO_CANCELADA")

    assert cancelada["status"] == "CANCELADA"
    assert evento_cancelada["resultado"] == "ALERTA"
    assert "cancelada" in evento_cancelada["descricao"]


def test_sessao_submissao_transicao_invalida_nao_cria_evento(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-ses-evt-invalid")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão inválida sem evento")
    eventos_antes = listar_eventos_sessao(client, processo["id"], sessao["id"])

    invalida = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "RECEBIDA"})
    eventos_depois = listar_eventos_sessao(client, processo["id"], sessao["id"])

    assert invalida.status_code == 422
    assert eventos_depois == eventos_antes
    assert [item["tipo_evento"] for item in eventos_depois] == ["SESSAO_INICIADA"]


def test_maquina_estado_sessao_submissao_valida_transicoes_e_campos(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-ses-state")
    acordo = create_acordo(client, processo["id"], titulo="Acordo vigente")
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão com estado")

    invalida = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "RECEBIDA"})
    transferencia = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "EM_TRANSFERENCIA"})
    recebida_sem_volume = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "RECEBIDA"})
    recebida = client.patch(
        f"/api/v1/admissao/sessoes/{sessao['id']}/status",
        json={"status": "RECEBIDA", "volume_recebido": "12 GB"},
    )
    quarentena = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "EM_QUARENTENA"})
    validacao = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "EM_VALIDACAO"})
    validada_sem_resultado = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "VALIDADA"})
    validada = client.patch(
        f"/api/v1/admissao/sessoes/{sessao['id']}/status",
        json={"status": "VALIDADA", "resultado_validacao": "Fixidez e estrutura conferidas."},
    )
    finalizada_direta = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "FINALIZADA"})
    normalizando = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "NORMALIZANDO"})
    normalizada = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "NORMALIZADA"})
    finalizada = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "FINALIZADA"})
    cancelar_finalizada = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "CANCELADA"})
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")

    assert invalida.status_code == 422
    assert transferencia.status_code == 200
    assert recebida_sem_volume.status_code == 422
    assert recebida.status_code == 200
    assert recebida.json()["volume_recebido"] == "12 GB"
    assert quarentena.status_code == 200
    assert validacao.status_code == 200
    assert validada_sem_resultado.status_code == 422
    assert validada.status_code == 200
    assert validada.json()["resultado_validacao"] == "Fixidez e estrutura conferidas."
    assert finalizada_direta.status_code == 422
    assert normalizando.status_code == 200
    assert normalizando.json()["status"] == "NORMALIZANDO"
    assert normalizada.status_code == 200
    assert normalizada.json()["status"] == "NORMALIZADA"
    assert finalizada.status_code == 200
    assert finalizada.json()["data_fim"] is not None
    assert cancelar_finalizada.status_code == 422
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
    assert any("transferência iniciada" in descricao for descricao in descricoes)
    assert any("transferência finalizada" in descricao for descricao in descricoes)
    assert any("quarentena iniciada" in descricao for descricao in descricoes)
    assert any("quarentena finalizada" in descricao for descricao in descricoes)
    assert any("validação iniciada" in descricao for descricao in descricoes)
    assert any("validação concluída com aprovação" in descricao for descricao in descricoes)
    assert any("normalização iniciada" in descricao for descricao in descricoes)
    assert any("normalização finalizada" in descricao for descricao in descricoes)
    assert any("finalizada" in descricao for descricao in descricoes)


def test_maquina_estado_sessao_submissao_fluxo_rejeitada_finaliza_sem_normalizacao(client: TestClient, unique_code: str):
    processo = create_processo(client, f"{unique_code}-ses-rej")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo="Sessão rejeitada")

    alterar_status_sessao(client, sessao["id"], "EM_TRANSFERENCIA")
    alterar_status_sessao(client, sessao["id"], "RECEBIDA", volume_recebido="8 GB")
    alterar_status_sessao(client, sessao["id"], "EM_QUARENTENA")
    alterar_status_sessao(client, sessao["id"], "EM_VALIDACAO")
    rejeitada = alterar_status_sessao(
        client,
        sessao["id"],
        "REJEITADA",
        resultado_validacao="Manifesto ausente.",
    )
    normalizando = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "NORMALIZANDO"})
    finalizada = alterar_status_sessao(client, sessao["id"], "FINALIZADA")
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")

    assert rejeitada["status"] == "REJEITADA"
    assert rejeitada["resultado_validacao"] == "Manifesto ausente."
    assert normalizando.status_code == 422
    assert finalizada["status"] == "FINALIZADA"
    assert finalizada["data_fim"] is not None
    descricoes = [item["descricao"] for item in eventos.json()]
    tipos_evento = [item["tipo_evento"] for item in eventos.json()]
    assert "SESSAO_REJEITADA" in tipos_evento
    assert "SESSAO_FINALIZADA" in tipos_evento
    assert "SESSAO_NORMALIZANDO" not in tipos_evento
    assert any("validação concluída com rejeição" in descricao for descricao in descricoes)
    assert any("finalizada" in descricao for descricao in descricoes)


@pytest.mark.parametrize(
    "estado_anterior",
    [
        "INICIADA",
        "EM_TRANSFERENCIA",
        "RECEBIDA",
        "EM_QUARENTENA",
        "EM_VALIDACAO",
        "VALIDADA",
        "REJEITADA",
        "NORMALIZANDO",
        "NORMALIZADA",
    ],
)
def test_sessao_submissao_pode_cancelar_em_todos_estados_antes_de_finalizar(
    client: TestClient,
    unique_code: str,
    estado_anterior: str,
):
    processo = create_processo(client, f"{unique_code}-ses-cancel-{estado_anterior.lower().replace('_', '-')}")
    acordo = create_acordo(client, processo["id"])
    sessao = create_sessao(client, processo["id"], acordo["id"], titulo=f"Sessão cancelar {estado_anterior}")

    if estado_anterior == "REJEITADA":
        alterar_status_sessao(client, sessao["id"], "EM_TRANSFERENCIA")
        alterar_status_sessao(client, sessao["id"], "RECEBIDA", volume_recebido="7 GB")
        alterar_status_sessao(client, sessao["id"], "EM_QUARENTENA")
        alterar_status_sessao(client, sessao["id"], "EM_VALIDACAO")
        alterar_status_sessao(client, sessao["id"], "REJEITADA", resultado_validacao="Rejeitada para teste.")
    elif estado_anterior != "INICIADA":
        avancar_sessao_ate_estado(client, sessao["id"], estado_anterior)

    cancelada = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "CANCELADA"})
    proxima = client.patch(f"/api/v1/admissao/sessoes/{sessao['id']}/status", json={"status": "EM_TRANSFERENCIA"})
    eventos = client.get(f"/api/v1/admissao/processos/{processo['id']}/eventos")

    assert cancelada.status_code == 200
    assert cancelada.json()["status"] == "CANCELADA"
    assert proxima.status_code == 422
    assert any("cancelada" in item["descricao"] for item in eventos.json())
    assert any(item["tipo_evento"] == "SESSAO_CANCELADA" for item in eventos.json())
