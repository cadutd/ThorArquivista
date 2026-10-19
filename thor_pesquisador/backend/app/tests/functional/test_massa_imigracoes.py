import uuid
from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.db.mongo import registros_collection, snapshots_collection
from app.db.session import SessionLocal
from app.main import create_app
from app.models.editorial import EditorialRegistro, EventoEditorial
from app.models.instrumento import Instrumento
from app.models.user import Usuario
from app.schemas.registro import RegistroUpdate
from app.scripts import seed_imigracoes as seed
from app.services import registro_service, instrumento_service, publicacao_service
from app.tests.functional.test_portal import visitante


@pytest.fixture
def context(monkeypatch):
    monkeypatch.setattr(seed, "INSTRUMENTO_ID", uuid.uuid4())
    monkeypatch.setattr(seed, "NOME", seed.NOME + " " + seed.INSTRUMENTO_ID.hex[:8])
    monkeypatch.setattr(registro_service, "enqueue_registro", lambda *a, **k: None)
    monkeypatch.setattr(instrumento_service, "enqueue_indexacao", lambda *a, **k: None)
    client = TestClient(create_app())
    response = client.post("/api/v1/auth/dev-login")
    assert response.status_code == 200
    return uuid.UUID(response.json()["id"])


def test_dados_repetiveis_e_diversificados():
    data = [seed.dados_registro(i) for i in range(1, 201)]
    assert data == [seed.dados_registro(i) for i in range(1, 201)]
    assert len({row["codigo_registro"] for row in data}) == 200
    assert len({row["nacionalidade"] for row in data}) == 10
    assert len({row["porto_chegada"] for row in data}) == 6
    for row in data:
        assert date(1880, 1, 1) <= date.fromisoformat(row["data_chegada"]) < date(1934, 1, 1)
        assert 1 <= row["idade_chegada"] <= 75
        assert row["nome"] and row["nome_mae"] and row["observacoes"] == seed.OBSERVACAO
    assert {field.chave for field in seed.campos()} == set(data[0])


def test_publica_com_agente_sem_duplicar_e_consulta_exige_sessao(context):
    with SessionLocal() as db:
        outside = list(db.execute(select(Instrumento.id, Instrumento.nome, Instrumento.status, Instrumento.visibilidade)
            .where(Instrumento.id != seed.INSTRUMENTO_ID).order_by(Instrumento.id)))
        first = seed.seed_imigracoes(db, context, quantidade=25, publicar_registros=True)
        assert first["criados"] == first["publicados_nesta_execucao"] == 25
        assert first["campos_criados"] == 9
        inst = db.get(Instrumento, seed.INSTRUMENTO_ID)
        assert inst.visibilidade == "PUBLICO" and inst.status == "PUBLICADO" and inst.publicacao_id
        events = db.scalar(select(func.count()).select_from(EventoEditorial).where(
            EventoEditorial.instrumento_id == inst.id))
        second = seed.seed_imigracoes(db, context, quantidade=25, publicar_registros=True)
        assert second["criados"] == second["campos_criados"] == second["publicados_nesta_execucao"] == 0
        assert second["existentes"] == second["total_registros"] == 25
        assert db.scalar(select(func.count()).select_from(EventoEditorial).where(
            EventoEditorial.instrumento_id == inst.id)) == events
        assert all(event.usuario_id == context and event.agente != "sistema" for event in db.scalars(
            select(EventoEditorial).where(EventoEditorial.instrumento_id == inst.id)))
        assert snapshots_collection().count_documents({"instrumento_id": str(inst.id)}) == 25
        assert outside == list(db.execute(select(Instrumento.id, Instrumento.nome, Instrumento.status, Instrumento.visibilidade)
            .where(Instrumento.id != seed.INSTRUMENTO_ID).order_by(Instrumento.id)))
        for _ in range(60):
            if not publicacao_service.processar_pendente(db, instrumento_id=inst.id):
                break
    client, _, _ = visitante()
    path = "/api/v1/publico/instrumentos/" + str(seed.INSTRUMENTO_ID)
    anonymous = TestClient(create_app())
    assert anonymous.get(path + "/buscar").status_code == 401
    assert str(seed.INSTRUMENTO_ID) in [row["id"] for row in anonymous.get(
        "/api/v1/publico/instrumentos", params={"q":seed.NOME}).json()["items"]]
    response = client.get(path + "/buscar?limit=20")
    assert response.status_code == 200, response.text
    page = response.json()
    assert page["total"] == 25 and len(page["items"]) == 20
    assert len(client.get(path + "/buscar?limit=20&offset=20").json()["items"]) == 5
    result = client.post(path + "/buscar", json={"q":"Giovanni"}).json()
    assert result["total"] == 1
    assert result["items"][0]["dados"] == seed.dados_registro(1)
    facets = client.get(path + "/facetas").json()
    assert "dados.nacionalidade" in facets and "dados.porto_chegada" in facets
    assert client.post(path + "/buscar", json={"filtros":{"nacionalidade":"Japonesa"}}).json()["total"] > 0


def test_sem_flag_nao_publica_e_preserva_edicao_inclusive_do_codigo(context):
    with SessionLocal() as db:
        first = seed.seed_imigracoes(db, context, quantidade=2)
        inst = db.get(Instrumento, seed.INSTRUMENTO_ID)
        assert first["publicados_nesta_execucao"] == 0 and not inst.publicacao_id
        doc = registros_collection().find_one({"instrumento_id": str(inst.id)})
        changed = {**doc["dados"], "nome":"Nome alterado manualmente", "codigo_registro":"CODIGO-MANUAL"}
        registro_service.atualizar_registro(db, inst.id, doc["_id"],
            RegistroUpdate(dados=changed, versao=1), context)
        second = seed.seed_imigracoes(db, context, quantidade=2, publicar_registros=True)
        assert second["criados"] == 0 and second["preservados"] == 1
        assert second["publicados_nesta_execucao"] == 1
        assert registros_collection().find_one({"_id":doc["_id"]})["dados"] == changed
        control = db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == doc["_id"]))
        assert control.status_editorial == "RASCUNHO" and not control.snapshot_id
        original = inst.nome
        inst.nome = "Nome personalizado"; db.commit()
        with pytest.raises(ValueError, match="alterado"):
            seed.seed_imigracoes(db, context, quantidade=2)
        assert inst.nome == "Nome personalizado"
        inst.nome = original; db.commit()
        field = inst.campos[0]; field.exibir_publico = False; db.commit()
        with pytest.raises(ValueError, match="Campo existente alterado"):
            seed.seed_imigracoes(db, context, quantidade=2)
        assert not field.exibir_publico


def test_nao_cria_privilegios_para_usuario_sem_permissoes(context):
    with SessionLocal() as db:
        actor = Usuario(nome="Sem concessoes para massa")
        db.add(actor); db.commit()
        with pytest.raises(HTTPException) as failure:
            seed.seed_imigracoes(db, actor.id, quantidade=1, publicar_registros=True)
        assert failure.value.status_code == 403
        assert db.get(Instrumento, seed.INSTRUMENTO_ID) is None


@pytest.mark.parametrize("environment", ["prod", "homolog", "production"])
def test_recusa_ambiente_operacional(monkeypatch, environment):
    monkeypatch.setattr(settings, "app_env", environment)
    with pytest.raises(ValueError, match="somente em dev/test"):
        seed.seed_imigracoes(None, None)


@pytest.mark.parametrize("quantity", [0, 1001])
def test_recusa_volume_invalido(monkeypatch, quantity):
    monkeypatch.setattr(settings, "app_env", "test")
    with pytest.raises(ValueError, match="Limites"):
        seed.seed_imigracoes(None, None, quantidade=quantity)
