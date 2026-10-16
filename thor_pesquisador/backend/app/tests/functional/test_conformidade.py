import csv
import io
import json
import uuid
from datetime import UTC, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from app.main import create_app
from app.core.config import settings
from app.db.mongo import registros_collection, snapshots_collection
from app.db.session import SessionLocal
from app.models.conformidade import AuditoriaGeral, Exportacao, ExecucaoRetencao, PoliticaRetencao
from app.models.editorial import EditorialRegistro, EventoEditorial
from app.models.imagem import AuditoriaImagem
from app.tests.functional.test_editorial import ctx, publish
from app.tests.functional.test_administracao import user_client
from app.tests.functional.test_permissoes_crud import grant
from app.services import exportacao_service as exports, retencao_service as retention


def request_export(client, iid, **kw):
    payload = {"operacao_id": str(uuid.uuid4()), "formato": "JSON", "escopo": "ADMINISTRATIVO", **kw}
    response = client.post("/api/v1/instrumentos/" + iid + "/exportacoes", json=payload)
    assert response.status_code == 202, response.text
    return response.json(), payload


def run_export(jid):
    # Isolate the job being tested from historical fixtures in the persistent test volume.
    with SessionLocal() as db:
        for _ in range(1000):
            if not exports.processar_pendente(db):
                break
            job = db.get(Exportacao, uuid.UUID(jid), populate_existing=True)
            if job.status not in {"PENDENTE", "PROCESSANDO"}:
                return job.status
        raise AssertionError("Job nao processado")


def policy(client, iid=None, **kw):
    data = {"nome": "Teste retencao " + uuid.uuid4().hex, "categoria": "REGISTRO_EXCLUIDO" if iid else "LOG_TECNICO",
            "dias": 1, "instrumento_id": iid, **kw}
    response = client.post("/api/v1/retencao/politicas", json=data)
    assert response.status_code == 201, response.text
    return response.json()


def run_retention(jid):
    with SessionLocal() as db:
        for _ in range(1000):
            if not retention.processar_pendente(db):
                break
            job = db.get(ExecucaoRetencao, uuid.UUID(jid), populate_existing=True)
            if job.status not in {"PENDENTE", "PROCESSANDO"}:
                return job
    raise AssertionError("Retencao nao processada")


def request_retention(client, pid, simulated=True):
    response = client.post("/api/v1/retencao/politicas/" + pid + "/execucoes",
        json={"operacao_id": str(uuid.uuid4()), "simulacao": simulated})
    assert response.status_code == 202, response.text
    return response.json()


@pytest.mark.parametrize("format", ["JSON", "CSV"])
def test_exportacao_real_s3_checkpoint_e_download(ctx, monkeypatch, format):
    admin, iid, rid = ctx
    monkeypatch.setattr(settings, "exportacao_batch_size", 1)
    path = "/api/v1/instrumentos/" + iid
    assert admin.put(path + "/registros/" + rid, json={"dados": {"titulo": "=1+1", "segredo": "interno"}}).status_code == 200
    assert admin.post(path + "/registros", json={"dados": {"titulo": 'Aspas, "ok"\nlinha'}}).status_code == 201
    job, payload = request_export(admin, iid, formato=format)
    assert admin.post(path + "/exportacoes", json=payload).json()["id"] == job["id"]
    assert run_export(job["id"]) == "CONCLUIDA"
    detail = admin.get("/api/v1/exportacoes/" + job["id"]).json()
    assert detail["processados"] == 2 and detail["partes"] == 2 and detail["checksum"]
    response = admin.get("/api/v1/exportacoes/" + job["id"] + "/download")
    assert response.status_code == 200 and len(response.content) == detail["tamanho_bytes"]
    assert "object_key" not in detail and "schema_json" not in detail
    if format == "JSON":
        data = response.json()
        assert len(data["registros"]) == 2 and data["schema"]["campos"]
    else:
        rows = list(csv.reader(io.StringIO(response.text)))
        assert len(rows) == 3 and "'=1+1" in [cell for row in rows for cell in row]


def test_pacote_so_snapshot_campos_publicos_sem_uris(ctx):
    admin, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid
    publish(admin, base)
    publish(admin, base + "/registros/" + rid)
    job, _ = request_export(admin, iid, formato="PACOTE", escopo="PUBLICADO")
    assert run_export(job["id"]) == "CONCLUIDA"
    data = admin.get("/api/v1/exportacoes/" + job["id"] + "/download").json()
    assert data["registros"][0]["dados"] == {"titulo": "Aprovado"}
    assert "CONFIDENCIAL" not in json.dumps(data)
    assert data["registros"][0]["imagens"] == []


def test_exportacao_erro_retomada_sem_duplicar(ctx, monkeypatch):
    admin, iid, _ = ctx
    job, _ = request_export(admin, iid)
    original = exports.armazenamento.salvar_fluxo
    monkeypatch.setattr(exports.armazenamento, "salvar_fluxo", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("segredo-S3")))
    assert run_export(job["id"]) == "FALHOU"
    detail = admin.get("/api/v1/exportacoes/" + job["id"]).json()
    assert detail["partes"] == 1 and "segredo-S3" not in detail["erro"]
    assert admin.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 410
    monkeypatch.setattr(exports.armazenamento, "salvar_fluxo", original)
    assert admin.post("/api/v1/exportacoes/" + job["id"] + "/repetir").status_code == 202
    assert run_export(job["id"]) == "CONCLUIDA"
    assert len(admin.get("/api/v1/exportacoes/" + job["id"] + "/download").json()["registros"]) == 1


def test_cancelamento_concorrente_nao_ressuscita_job(ctx, monkeypatch):
    admin, iid, _ = ctx
    job, _ = request_export(admin, iid)
    original = exports.armazenamento.salvar_upload
    def cancelling(*args, **kwargs):
        assert admin.delete("/api/v1/exportacoes/" + job["id"]).status_code == 200
        return original(*args, **kwargs)
    monkeypatch.setattr(exports.armazenamento, "salvar_upload", cancelling)
    assert run_export(job["id"]) == "CANCELADA"
    assert admin.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 410
    assert admin.post("/api/v1/exportacoes/" + job["id"] + "/repetir").status_code == 409
    assert admin.delete("/api/v1/exportacoes/" + job["id"]).status_code == 200


def test_alteracao_dados_e_expiracao_bloqueiam_arquivo(ctx):
    admin, iid, rid = ctx
    job, _ = request_export(admin, iid)
    assert run_export(job["id"]) == "CONCLUIDA"
    assert admin.put("/api/v1/instrumentos/" + iid + "/registros/" + rid, json={"dados": {"titulo": "Novo"}}).status_code == 200
    assert admin.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 409
    job2, _ = request_export(admin, iid)
    with SessionLocal() as db:
        db.get(Exportacao, uuid.UUID(job2["id"])).expira_em = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    assert run_export(job2["id"]) == "EXPIRADA"
    assert admin.get("/api/v1/exportacoes/" + job2["id"] + "/download").status_code == 410


def test_auditoria_unificada_append_only_ator_e_correlacao(ctx):
    admin, iid, _ = ctx
    reqid = str(uuid.uuid4())
    response = admin.put("/api/v1/instrumentos/" + iid, json={"nome": "Nome atualizado"},
                         headers={"X-Request-ID": reqid})
    assert response.headers["x-request-id"] == reqid
    page = admin.get("/api/v1/auditoria", params={"instrumento_id": iid}).json()
    assert page["total"] >= 1
    matches = [e for e in page["items"] if e["request_id"] == reqid and e["entidade"] == "instrumento"]
    assert len(matches) == 1
    event = matches[0]
    assert event["agente"] == "Usuario Desenvolvimento" and event["entidade"] == "instrumento"
    assert "Nome atualizado" not in json.dumps(event) and "cpf" not in json.dumps(event["detalhe"])
    assert admin.get("/api/v1/auditoria/" + event["fonte"] + "/" + event["id"]).status_code == 200
    with SessionLocal() as db:
        with pytest.raises(DBAPIError):
            table = {"geral": "auditoria_geral", "editorial": "eventos_editoriais", "imagem": "auditoria_imagens"}[event["fonte"]]
            db.execute(text("DELETE FROM " + table + " WHERE id=:id"), {"id": uuid.UUID(event["id"])})
        db.rollback()
    assert admin.delete("/api/v1/auditoria/geral/" + event["id"]).status_code == 405


def test_novos_modulos_exigem_sessao_e_permissoes(ctx):
    admin, iid, _ = ctx
    anon = TestClient(create_app())
    actor, user = user_client()
    for path in ("/auditoria", "/exportacoes", "/retencao/politicas", "/retencao/execucoes", "/relatorios"):
        assert anon.get("/api/v1" + path).status_code == 401
        assert actor.get("/api/v1" + path).status_code == 403
    job, _ = request_export(admin, iid)
    grant(admin, user, ["exportacoes_consultar"], iid)
    assert actor.get("/api/v1/exportacoes").json()["total"] == 0
    assert actor.get("/api/v1/exportacoes/" + job["id"]).status_code == 403
    assert actor.post("/api/v1/instrumentos/" + iid + "/exportacoes", json={"operacao_id": str(uuid.uuid4())}).status_code == 403


def test_revogacao_no_worker_e_download(ctx):
    admin, iid, _ = ctx
    actor, user = user_client()
    _, access = grant(admin, user, ["exportacoes_incluir", "exportacoes_consultar", "registros_consultar"], iid)
    job, _ = request_export(actor, iid)
    assert admin.delete("/api/v1/acessos/" + access).status_code == 200
    assert run_export(job["id"]) == "FALHOU"
    assert actor.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 403


def test_retencao_simulacao_bloqueios_snapshot_e_expurgo(ctx, monkeypatch):
    admin, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid
    assert admin.delete(base + "/registros/" + rid).status_code == 200
    with SessionLocal() as db:
        row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid))
        row.atualizado_em = datetime.now(UTC) - timedelta(days=10)
        db.commit()
    p = policy(admin, iid, permitir_expurgo=True)
    sim = request_retention(admin, p["id"])
    done = run_retention(sim["id"])
    assert done.status == "CONCLUIDA" and done.elegiveis == 1 and done.removidos == 0
    assert registros_collection().find_one({"_id": rid})
    assert admin.put(base + "/registros/" + rid + "/retencao", json={"bloqueado": True}).status_code == 200
    with SessionLocal() as db:
        row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid))
        row.atualizado_em = datetime.now(UTC) - timedelta(days=10)
        db.commit()
    sim = request_retention(admin, p["id"])
    assert run_retention(sim["id"]).bloqueados == 1
    assert admin.put(base + "/registros/" + rid + "/retencao", json={"bloqueado": False}).status_code == 200
    with SessionLocal() as db:
        row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid))
        row.atualizado_em = datetime.now(UTC) - timedelta(days=10)
        db.commit()
    from app.services import indexacao_service
    monkeypatch.setattr(indexacao_service, "_meili_request", lambda *a, **kw: {})
    actual = request_retention(admin, p["id"], False)
    done = run_retention(actual["id"])
    assert done.status == "CONCLUIDA" and done.removidos == 1
    assert not registros_collection().find_one({"_id": rid})
    with SessionLocal() as db:
        assert db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid)).expurgado_em
        assert db.scalar(select(EventoEditorial.id).where(EventoEditorial.registro_id == rid))
    sim = request_retention(admin, p["id"])
    assert run_retention(sim["id"]).removidos == 0


def test_retencao_nao_apaga_snapshot_historico(ctx):
    admin, iid, rid = ctx
    base = "/api/v1/instrumentos/" + iid
    publish(admin, base); publish(admin, base + "/registros/" + rid)
    assert admin.delete(base + "/registros/" + rid).status_code == 200
    with SessionLocal() as db:
        db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == rid)).atualizado_em = datetime.now(UTC) - timedelta(days=10)
        db.commit()
    p = policy(admin, iid, permitir_expurgo=True)
    job = request_retention(admin, p["id"], False)
    done = run_retention(job["id"])
    assert done.status == "CONCLUIDA" and done.bloqueados == 1 and done.removidos == 0
    assert snapshots_collection().find_one({"registro_id": rid}) and registros_collection().find_one({"_id": rid})


def test_politica_desativacao_cancelamento_e_repeticao(ctx):
    admin, _, _ = ctx
    p = policy(admin)
    assert admin.post("/api/v1/retencao/politicas/" + p["id"] + "/execucoes",
                      json={"operacao_id": str(uuid.uuid4()), "simulacao": False}).status_code == 409
    job = request_retention(admin, p["id"])
    assert admin.delete("/api/v1/retencao/politicas/" + p["id"]).status_code == 409
    assert admin.delete("/api/v1/retencao/execucoes/" + job["id"]).status_code == 200
    assert admin.delete("/api/v1/retencao/execucoes/" + job["id"]).status_code == 200
    assert admin.post("/api/v1/retencao/execucoes/" + job["id"] + "/repetir").status_code == 409
    assert admin.delete("/api/v1/retencao/politicas/" + p["id"]).json()["ativo"] is False


def test_worker_recupera_lease_e_checkpoint_apos_queda(ctx, monkeypatch):
    admin, iid, _ = ctx
    monkeypatch.setattr(settings, "exportacao_batch_size", 1)
    for title in ("segundo", "terceiro"):
        assert admin.post("/api/v1/instrumentos/" + iid + "/registros", json={"dados": {"titulo": title}}).status_code == 201
    job, _ = request_export(admin, iid)
    original = exports.armazenamento.salvar_upload
    calls = []
    class Crash(BaseException):
        pass
    def crash(*args, **kw):
        calls.append(1)
        if len(calls) == 2:
            raise Crash()
        return original(*args, **kw)
    monkeypatch.setattr(exports.armazenamento, "salvar_upload", crash)
    with SessionLocal() as db:
        with pytest.raises(Crash):
            exports.processar_pendente(db)
    with SessionLocal() as db:
        row = db.get(Exportacao, uuid.UUID(job["id"]))
        assert row.status == "PROCESSANDO" and row.processados == 1 and row.checkpoint
        row.lease_ate = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    monkeypatch.setattr(exports.armazenamento, "salvar_upload", original)
    assert run_export(job["id"]) == "CONCLUIDA"
    data = admin.get("/api/v1/exportacoes/" + job["id"] + "/download").json()
    assert len({r["id"] for r in data["registros"]}) == 3


def test_falha_mongo_e_falha_sql_nao_liberam_arquivo(ctx, monkeypatch):
    admin, iid, _ = ctx
    job, _ = request_export(admin, iid)
    monkeypatch.setattr(exports, "registros_collection", lambda: (_ for _ in ()).throw(RuntimeError("senha-do-mongo")))
    assert run_export(job["id"]) == "FALHOU"
    result = admin.get("/api/v1/exportacoes/" + job["id"]).json()
    assert result["processados"] == 0 and "senha-do-mongo" not in json.dumps(result)


def test_exportacao_solicitacao_concorrente_idempotente(ctx):
    admin, iid, _ = ctx
    payload = {"operacao_id": str(uuid.uuid4()), "formato": "JSON", "escopo": "ADMINISTRATIVO"}
    cookie = dict(admin.cookies)
    def create(_):
        client = TestClient(create_app())
        client.cookies.update(cookie)
        return client.post("/api/v1/instrumentos/" + iid + "/exportacoes", json=payload)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(create, range(2)))
    assert all(r.status_code == 202 for r in responses)
    assert responses[0].json()["id"] == responses[1].json()["id"]


def test_desativacao_perfil_impede_download_ja_concluido(ctx):
    admin, iid, _ = ctx
    actor, user = user_client()
    profile, _ = grant(admin, user, ["exportacoes_consultar", "exportacoes_incluir", "registros_consultar"], iid)
    job, _ = request_export(actor, iid)
    assert run_export(job["id"]) == "CONCLUIDA"
    assert actor.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 200
    assert admin.delete("/api/v1/perfis/" + profile).status_code == 200
    assert actor.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 403


def test_imagens_eventos_existentes_sem_copia_e_sem_duplicacao(ctx):
    admin, iid, rid = ctx
    result = admin.post("/api/v1/imagens", json={"titulo": "Auditavel", "uri": "https://example.org/a.jpg"})
    assert result.status_code == 201
    image = result.json()["id"]
    with SessionLocal() as db:
        ids = set(db.scalars(select(AuditoriaImagem.id).where(AuditoriaImagem.imagem_id == uuid.UUID(image))))
        assert ids and not db.scalar(select(AuditoriaGeral.id).where(AuditoriaGeral.entidade_id == image))
    page = admin.get("/api/v1/auditoria?entidade=imagem").json()
    assert ids.issubset({uuid.UUID(e["id"]) for e in page["items"]})


@pytest.mark.parametrize("field,value", [("bloqueada", True), ("ativo", False)])
def test_retencao_nega_politicas_indisponiveis(ctx, field, value):
    admin, _, _ = ctx
    p = policy(admin, **{field: value})
    assert admin.post("/api/v1/retencao/politicas/" + p["id"] + "/execucoes",
                     json={"operacao_id": str(uuid.uuid4())}).status_code == 409


def test_limpeza_artefato_expirado_preserva_job_e_auditoria(ctx):
    admin, iid, _ = ctx
    job, _ = request_export(admin, iid)
    assert run_export(job["id"]) == "CONCLUIDA"
    with SessionLocal() as db:
        row = db.get(Exportacao, uuid.UUID(job["id"]))
        row.expira_em = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
        retention.expirar_exportacoes(db, limit=1000)
        retention.limpar_artefatos(db, limit=1000)
        row = db.get(Exportacao, uuid.UUID(job["id"]), populate_existing=True)
        assert row.status == "EXPIRADA" and row.object_key is None and row.ultimo_descarte_em
        assert db.scalar(select(AuditoriaGeral.id).where(AuditoriaGeral.entidade_id == job["id"]))
    assert admin.get("/api/v1/exportacoes/" + job["id"] + "/download").status_code == 410


def test_relatorios_filtros_paginacao_e_privacidade(ctx):
    admin, iid, _ = ctx
    data = admin.get("/api/v1/relatorios", params={"instrumento_id": iid}).json()
    assert data["registros"] == [{"nome": "ATIVO", "total": 1}]
    page = admin.get("/api/v1/relatorios/registros", params={"instrumento_id": iid, "limit": 1}).json()
    assert page["total"] == 1 and page["items"][0]["total"] == 1
    assert admin.get("/api/v1/relatorios?inicio=2000-01-01T00:00:00Z").status_code == 422
    actor, user = user_client()
    grant(admin, user, ["relatorios_consultar", "auditoria_consultar"], iid)
    assert actor.get("/api/v1/relatorios").status_code == 200
    assert actor.get("/api/v1/relatorios/usuarios").status_code == 403
    events = actor.get("/api/v1/auditoria").json()
    assert all(e["instrumento_id"] == iid and e["entidade"] not in {"usuario", "perfil", "acesso"} for e in events["items"])
