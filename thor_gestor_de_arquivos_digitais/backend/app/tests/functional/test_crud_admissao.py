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


@pytest.mark.parametrize("field", ["id_acordo_utilizado", "titulo", "data_inicio", "canal_submissao", "tipo_suporte"])
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
