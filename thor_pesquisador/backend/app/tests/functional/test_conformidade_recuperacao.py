import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.conformidade import AuditoriaGeral, ExecucaoRetencao, Exportacao, LogRequisicao
from app.models.editorial import EditorialRegistro
from app.models.user import Usuario
from app.schemas.conformidade import ExportacaoIn
from app.services import exportacao_service as exports, retencao_service as retention
from app.services.armazenamento_service import armazenamento
from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_conformidade import request_export, run_export, policy, request_retention, run_retention
from app.tests.functional.test_administracao import user_client
from app.tests.functional.test_permissoes_crud import grant
from app.main import create_app


def test_s3_multipart_real_checksum_e_memoria_limitada():
    assert settings.mongodb_database.endswith("_test")
    key = "teste-fase5/" + str(uuid.uuid4())
    block = b"a" * (1024 * 1024)
    try:
        checksum, size = armazenamento.salvar_fluxo(key, (block for _ in range(20)), "application/octet-stream")
        assert size == 20 * len(block)
        expected = hashlib.sha256()
        for _ in range(20):
            expected.update(block)
        assert checksum == expected.hexdigest()
        obj = armazenamento.obter_objeto(key)["Body"]
        actual, count = hashlib.sha256(), 0
        try:
            for chunk in obj.iter_chunks(chunk_size=1024 * 1024):
                actual.update(chunk); count += len(chunk)
        finally:
            obj.close()
        assert count == size and actual.hexdigest() == checksum
    finally:
        armazenamento.remover_objeto(key)


def test_falha_sql_reverte_solicitacao_e_auditoria(ctx, monkeypatch):
    admin, iid, _ = ctx
    op = uuid.uuid4()
    with SessionLocal() as db:
        db.info["usuario"] = db.scalar(select(Usuario).where(Usuario.govbr_sub == "00000000000"))
        def fail():
            raise ConnectionError("falha SQL simulada")
        monkeypatch.setattr(db, "commit", fail)
        with pytest.raises(ConnectionError):
            exports.solicitar(db, uuid.UUID(iid), ExportacaoIn(operacao_id=op))
    with SessionLocal() as db:
        assert not db.scalar(select(Exportacao.id).where(Exportacao.operacao_id == op))
        assert not db.scalar(select(AuditoriaGeral.id).where(AuditoriaGeral.operacao_id == op))


def test_falha_fila_nao_impede_confirmar_job(ctx, monkeypatch):
    admin, iid, _ = ctx
    from app.services import indexacao_service
    monkeypatch.setattr(indexacao_service, "redis_client", lambda: (_ for _ in ()).throw(ConnectionError("Redis indisponivel")))
    job, _ = request_export(admin, iid)
    assert run_export(job["id"]) == "CONCLUIDA"


def test_valores_json_numeros_booleanos_e_listas(ctx):
    admin, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid
    for key, kind in (("numero", "NUMERO"), ("booleano", "BOOLEANO"), ("lista", "LISTA_MULTIPLA"), ("data", "DATA")):
        assert admin.post(base + "/campos", json={"nome": key, "chave": key, "tipo": kind}).status_code == 201
    values = {"titulo": "Tipos", "numero": -12.5, "booleano": False, "lista": ["a", "b"], "data": "2026-10-15"}
    assert admin.put(base + "/registros/" + rid, json={"dados": values}).status_code == 200
    job, _ = request_export(admin, iid)
    assert run_export(job["id"]) == "CONCLUIDA"
    assert admin.get("/api/v1/exportacoes/" + job["id"] + "/download").json()["registros"][0]["dados"] == values


def test_retencao_falha_retomada_preserva_checkpoint(ctx, monkeypatch):
    admin, iid, rid = ctx
    assert admin.delete("/api/v1/instrumentos/" + iid + "/registros/" + rid).status_code == 200
    with SessionLocal() as db:
        db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid)).atualizado_em = datetime.now(UTC) - timedelta(days=5)
        db.commit()
    p = policy(admin, iid, permitir_expurgo=True)
    job = request_retention(admin, p["id"], False)
    original = retention._remover
    monkeypatch.setattr(retention, "_remover", lambda *a: (_ for _ in ()).throw(ConnectionError("Falha de servico")))
    assert run_retention(job["id"]).status == "FALHOU"
    monkeypatch.setattr(retention, "_remover", original)
    assert admin.post("/api/v1/retencao/execucoes/" + job["id"] + "/repetir").status_code == 202
    from app.services import indexacao_service
    monkeypatch.setattr(indexacao_service, "_meili_request", lambda *a, **kw: {})
    result = run_retention(job["id"])
    assert result.status == "CONCLUIDA" and result.processados == 1 and result.removidos == 1


def test_retencao_revogacao_antes_execucao(ctx):
    admin, iid, _ = ctx
    p = policy(admin, iid)
    actor, user = user_client()
    _, access = grant(admin, user, ["retencao_consultar", "retencao_simular"], iid)
    job = request_retention(actor, p["id"])
    assert admin.delete("/api/v1/acessos/" + access).status_code == 200
    assert run_retention(job["id"]).status == "FALHOU"
    assert actor.get("/api/v1/retencao/execucoes/" + job["id"]).status_code == 403


def test_checagem_retencao_data_futura(ctx):
    admin, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid + "/registros/" + rid
    assert admin.delete(base).status_code == 200
    assert admin.put(base + "/retencao", json={"reter_ate": (datetime.now(UTC) + timedelta(days=5)).isoformat()}).status_code == 200
    with SessionLocal() as db:
        db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid)).atualizado_em = datetime.now(UTC) - timedelta(days=5)
        db.commit()
    p = policy(admin, iid, permitir_expurgo=True)
    job = request_retention(admin, p["id"], False)
    assert run_retention(job["id"]).bloqueados == 1


def test_logs_minimos_e_acesso_consultivo_opcional(ctx, monkeypatch):
    admin, iid, _ = ctx
    monkeypatch.setattr(settings, "log_acesso_consultivo", True)
    request_id = str(uuid.uuid4())
    secret = "CODIGO_OAUTH_NAO_LOGAR"
    anon = TestClient(create_app())
    response = anon.get("/api/v1/publico/instrumentos/" + iid + "?q=" + secret, headers={"X-Request-ID": request_id})
    assert response.status_code == 401
    with SessionLocal() as db:
        rows = db.scalars(select(LogRequisicao).where(LogRequisicao.request_id == request_id)).all()
        assert {r.categoria for r in rows} == {"LOG_TECNICO", "ACESSO_CONSULTIVO"}
        assert all(r.rota == "/api/v1/publico/instrumentos/{instrumento_id}" for r in rows)
        assert secret not in json.dumps([retention.serializar(r) for r in rows], default=str)


def test_expurgo_preserva_imagem_compartilhada_e_seu_historico(ctx, monkeypatch):
    admin, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid
    other = admin.post(base + "/registros", json={"dados": {"titulo": "Outro"}}).json()["id"]
    image = admin.post("/api/v1/imagens", json={"titulo": "Compartilhada", "uri": "https://example.org/comp.jpg",
                                             "direitos_acesso": "PUBLICO"}).json()["id"]
    for record in (rid, other):
        assert admin.post(base + "/registros/" + record + "/imagens", json={"imagem_id": image}).status_code == 201
    assert admin.delete(base + "/registros/" + rid).status_code == 200
    with SessionLocal() as db:
        db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid)).atualizado_em = datetime.now(UTC) - timedelta(days=5)
        db.commit()
    p = policy(admin, iid, permitir_expurgo=True)
    job = request_retention(admin, p["id"], False)
    from app.services import indexacao_service
    monkeypatch.setattr(indexacao_service, "_meili_request", lambda *a, **kw: {})
    assert run_retention(job["id"]).removidos == 1
    assert admin.get("/api/v1/imagens/" + image).status_code == 200
    assert admin.get(base + "/registros/" + other + "/imagens").json()["total"] == 1
    from app.models.imagem import AuditoriaImagem
    with SessionLocal() as db:
        assert db.scalar(select(AuditoriaImagem.id).where(AuditoriaImagem.registro_id == rid))


def test_exportacao_rejeita_documento_sem_controle_sql(ctx):
    admin, iid, rid = ctx
    with SessionLocal() as db:
        db.delete(db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid)))
        db.commit()
    job, _ = request_export(admin, iid)
    assert run_export(job["id"]) == "FALHOU"


def test_criacao_durante_exportacao_invalida_revisao(ctx, monkeypatch):
    admin, iid, _ = ctx
    from app.services import registro_service
    collection = registro_service.registros_collection()
    jobs = []
    class Creating:
        def insert_one(self, document):
            jobs.append(request_export(admin, iid)[0])
            return collection.insert_one(document)
    monkeypatch.setattr(registro_service, "registros_collection", lambda: Creating())
    response = admin.post("/api/v1/instrumentos/" + iid + "/registros", json={"dados": {"titulo": "Concorrente"}})
    assert response.status_code == 201
    assert run_export(jobs[0]["id"]) == "FALHOU"
