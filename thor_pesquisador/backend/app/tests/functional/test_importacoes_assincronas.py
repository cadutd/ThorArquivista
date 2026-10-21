import json
import uuid
from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.core.config import settings
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.main import create_app
from app.models.importacao_async import ImportacaoAsync as Job, ImportacaoAsyncParte as Parte
from app.models.editorial import AcessoInstrumento
from app.services import importacao_async_service as service, importacao_async_worker as worker
from app.services.armazenamento_service import armazenamento
from app.tests.functional.test_editorial import ctx as editorial_ctx
from app.tests.functional.test_importacoes import user_client


@pytest.fixture
def ctx(editorial_ctx):
    _, iid, rid = editorial_ctx
    client, _ = user_client(iid, ["registros_incluir", "registros_consultar",
        "instrumentos_consultar", "campos_incluir", "campos_consultar"])
    return client, iid, rid


def base(iid):
    return "/api/v1/instrumentos/" + iid + "/registros/importacoes/assincronas"


def start(client, iid, content, name="fonte.csv"):
    response = client.post(base(iid), json={"operacao_id": str(uuid.uuid4()), "nome_arquivo": name, "tamanho_bytes": len(content)})
    assert response.status_code == 201, response.text
    jid = response.json()["id"]
    size = settings.importacao_chunk_bytes
    for offset in range(0, len(content), size):
        part = client.post(base(iid) + "/" + jid + "/partes", params={"numero": offset // size + 1},
                          files={"arquivo": ("parte", content[offset:offset + size], "application/octet-stream")})
        assert part.status_code == 200, part.text
    queued = client.post(base(iid) + "/" + jid + "/finalizar")
    assert queued.status_code == 202, queued.text
    return jid


def run(jid):
    with SessionLocal() as db:
        assert worker.processar_pendente(db, job_id=uuid.UUID(jid))
        return service.saida(db.get(Job, uuid.UUID(jid)))


def get(client, iid, jid):
    response = client.get(base(iid) + "/" + jid)
    assert response.status_code == 200, response.text
    return response.json()


def validate(client, iid, jid, mappings=None):
    job = get(client, iid, jid)
    response = client.post(base(iid) + "/" + jid + "/validar", json={
        "operacao_id": jid, "schema_version": job["analise"]["schema_version"],
        "mapeamentos": mappings or [{"origem": "Nome", "destino": "titulo"}]})
    assert response.status_code == 202, response.text
    return run(jid)


def ready(client, iid, content=b"Nome\nAna\nMaria"):
    jid = start(client, iid, content)
    assert run(jid)["status"] == "AGUARDANDO_MAPA"
    assert validate(client, iid, jid)["status"] == "AGUARDANDO_CONFIRMACAO"
    return jid


def test_fluxo_assincrono_completo_e_idempotencia(ctx, monkeypatch):
    client, iid, _ = ctx
    monkeypatch.setattr(settings, "importacao_batch_size", 1)
    jid = start(client, iid, b"Nome\nAna\nMaria")
    assert registros_collection().count_documents({"instrumento_id": iid}) == 1
    initial = get(client, iid, jid)
    assert initial["status"] == "ANALISANDO"
    assert initial["analise"] is None and initial["configuracao"] is None and initial["relatorio"] is None
    assert run(jid)["status"] == "AGUARDANDO_MAPA"
    report = validate(client, iid, jid)
    assert report["validos"] == 2 and report["processados"] == 0
    assert client.post(base(iid) + "/" + jid + "/confirmar").status_code == 202
    assert get(client, iid, jid)["status"] == "PENDENTE"
    final = run(jid)
    assert final["status"] == "CONCLUIDA" and final["processados"] == 2
    docs = list(registros_collection().find({"_importacao_id": jid}))
    assert len(docs) == 2 and all(d["status"] == "ATIVO" for d in docs)
    for doc in docs:
        out = client.get("/api/v1/instrumentos/" + iid + "/registros/" + doc["_id"]).json()
        assert out["status_editorial"] == "RASCUNHO"
    assert client.post(base(iid) + "/" + jid + "/confirmar").json()["processados"] == 2
    assert registros_collection().count_documents({"_importacao_id": jid}) == 2
    assert "object_key" not in json.dumps(get(client, iid, jid))
    listing = client.get(base(iid), params={"q": "fonte", "status": "CONCLUIDA", "limit": 1}).json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == jid


def test_upload_em_partes_retoma_e_rejeita_troca(ctx, monkeypatch):
    client, iid, _ = ctx
    monkeypatch.setattr(settings, "importacao_chunk_bytes", 1024)
    content = b"Nome\n" + b"A" * 1500
    payload = {"operacao_id": str(uuid.uuid4()), "nome_arquivo": "a.csv", "tamanho_bytes": len(content)}
    job = client.post(base(iid), json=payload).json()
    path = base(iid) + "/" + job["id"]
    assert client.post(base(iid), json=payload).json()["id"] == job["id"]
    assert client.post(path + "/finalizar").status_code == 409
    def part(n, value):
        return client.post(path + "/partes", params={"numero": n}, files={"arquivo": ("a", value)})
    assert part(2, content[1024:]).status_code == 409
    assert part(1, content[:1024]).json()["bytes_recebidos"] == 1024
    assert part(1, content[:1024]).json()["bytes_recebidos"] == 1024
    assert part(1, b"B" * 1024).status_code == 409
    assert part(2, content[1024:]).json()["bytes_recebidos"] == len(content)
    assert client.post(path + "/finalizar").status_code == 202
    assert part(1, content[:1024]).status_code == 409


def test_recupera_indexacao_quando_fila_indisponivel(ctx, monkeypatch):
    from app.models.instrumento import IndexacaoJob
    from app.services import indexacao_service as indexing
    client, iid, _ = ctx
    jid = ready(client, iid)
    monkeypatch.setattr(worker, "enqueue_indexacao", lambda *a, **k: None)
    assert client.post(base(iid) + "/" + jid + "/confirmar").status_code == 202
    assert run(jid)["status"] == "CONCLUIDA"
    calls = []
    monkeypatch.setattr(indexing, "_reindexar", lambda db, job_id, instrument_id: calls.append((job_id, instrument_id)))
    with SessionLocal() as db:
        index = db.get(IndexacaoJob, uuid.uuid5(uuid.UUID(jid), "indexacao"))
        assert index.status == "PENDENTE"
        index.criado_em = datetime(2000, 1, 1, tzinfo=UTC)
        db.commit()
        assert indexing.recuperar_reindexacao_pendente(db)
        assert calls == [(index.id, uuid.UUID(iid))]
        db.refresh(index)
        assert index.status == "PROCESSANDO"


def test_mapeamento_campos_privados_e_erros_csv(ctx):
    client, iid, _ = ctx
    jid = start(client, iid, b"Nome,Idade\nAna,invalido")
    run(jid)
    mappings = [{"origem": "Nome", "destino": "titulo"},
                {"origem": "Idade", "novo": {"nome": "Idade", "chave": "idade", "tipo": "NUMERO"}}]
    result = validate(client, iid, jid, mappings)
    assert result["status"] == "ERROS_VALIDACAO" and result["invalidos"] == 1
    assert client.post(base(iid) + "/" + jid + "/confirmar").status_code == 409
    errors = client.get(base(iid) + "/" + jid + "/erros")
    assert errors.status_code == 200 and b"NUMERO" in errors.content
    assert not any(f["chave"] == "idade" for f in client.get("/api/v1/instrumentos/" + iid + "/schema").json()["campos"])
    mappings[-1]["novo"]["tipo"] = "TEXTO_CURTO"
    assert validate(client, iid, jid, mappings)["status"] == "AGUARDANDO_CONFIRMACAO"
    assert client.post(base(iid) + "/" + jid + "/confirmar").status_code == 202
    assert run(jid)["status"] == "CONCLUIDA"
    schema = client.get("/api/v1/instrumentos/" + iid + "/schema").json()
    assert not next(f for f in schema["campos"] if f["chave"] == "idade")["exibir_publico"]


def test_retomada_apos_mongo_antes_checkpoint(ctx, monkeypatch):
    from app.services import importacao_bulk
    client, iid, _ = ctx
    jid = ready(client, iid)
    client.post(base(iid) + "/" + jid + "/confirmar")
    original = importacao_bulk.gravar_lote
    def failing(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("Falha simulada antes do commit SQL")
    monkeypatch.setattr(importacao_bulk, "gravar_lote", failing)
    assert run(jid)["status"] == "FALHOU"
    assert registros_collection().count_documents({"_importacao_id": jid}) == 2
    monkeypatch.setattr(importacao_bulk, "gravar_lote", original)
    assert client.post(base(iid) + "/" + jid + "/retomar").status_code == 202
    assert run(jid)["processados"] == 2
    assert registros_collection().count_documents({"_importacao_id": jid}) == 2


def test_cancelamento_entre_lotes_preserva_confirmados(ctx, monkeypatch):
    client, iid, _ = ctx
    monkeypatch.setattr(settings, "importacao_batch_size", 1)
    jid = ready(client, iid)
    path = base(iid) + "/" + jid
    client.post(path + "/confirmar")
    original = service.ler_parte
    calls = []
    def cancel(part):
        calls.append(part.numero)
        if len(calls) == 2:
            assert client.post(path + "/cancelar").status_code == 200
        return original(part)
    monkeypatch.setattr(service, "ler_parte", cancel)
    assert run(jid)["status"] == "CANCELADA"
    assert get(client, iid, jid)["processados"] == 1
    assert registros_collection().count_documents({"_importacao_id": jid}) == 1
    assert client.post(path + "/retomar").status_code == 409


def test_lease_expirada_e_worker_antigo_bloqueado(ctx):
    client, iid, _ = ctx
    jid = start(client, iid, b"Nome\nAna")
    old = uuid.uuid4()
    with SessionLocal() as db:
        job = db.get(Job, uuid.UUID(jid))
        job.lease_token, job.lease_ate = old, datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    assert run(jid)["status"] == "AGUARDANDO_MAPA"
    with SessionLocal() as db:
        with pytest.raises(Exception):
            worker.verificar(db, uuid.UUID(jid), old)


def test_permissoes_propriedade_e_revogacao(ctx):
    admin, iid, _ = ctx
    anonymous = TestClient(create_app())
    assert anonymous.get(base(iid) + "/limites").status_code == 401
    client, gid = user_client(iid, ["registros_incluir", "instrumentos_consultar"])
    jid = start(client, iid, b"Nome\nAna")
    assert admin.get(base(iid) + "/" + jid).status_code == 404
    assert run(jid)["status"] == "AGUARDANDO_MAPA"
    cfg = {"operacao_id": jid, "schema_version": get(client, iid, jid)["analise"]["schema_version"],
           "mapeamentos": [{"origem": "Nome", "novo": {"nome": "X", "chave": "x", "tipo": "TEXTO_CURTO"}}]}
    assert client.post(base(iid) + "/" + jid + "/validar", json=cfg).status_code == 403
    with SessionLocal() as db:
        db.delete(db.get(AcessoInstrumento, gid)); db.commit()
    assert client.get(base(iid) + "/" + jid).status_code == 403


def test_schema_alterado_pausa_importacao(ctx):
    client, iid, _ = ctx
    jid = ready(client, iid)
    assert client.post(base(iid) + "/" + jid + "/confirmar").status_code == 202
    assert client.post("/api/v1/instrumentos/" + iid + "/campos",
        json={"nome": "Outro", "chave": "outro", "tipo": "TEXTO_CURTO"}).status_code == 201
    assert run(jid)["status"] == "PAUSADA"
    assert client.post(base(iid) + "/" + jid + "/retomar").status_code == 409
    assert registros_collection().count_documents({"_importacao_id": jid}) == 0


def test_expiracao_limpa_arquivos_mas_preserva_historico(ctx):
    client, iid, _ = ctx
    jid = ready(client, iid)
    with SessionLocal() as db:
        job = db.get(Job, uuid.UUID(jid))
        job.expira_em = datetime.now(UTC) - timedelta(days=1)
        db.commit()
        assert worker.limpar_expirado(db)
        db.refresh(job)
        assert job.status == "EXPIRADA" and job.limpo_em is not None
    assert get(client, iid, jid)["status"] == "EXPIRADA"
    assert client.post(base(iid) + "/" + jid + "/confirmar").status_code == 410
    response = armazenamento.client().list_objects_v2(Bucket=settings.s3_bucket, Prefix="importacoes-assincronas/" + jid + "/")
    assert response.get("KeyCount", 0) == 0


@pytest.mark.parametrize("content,name", [(b"a,b\n1", "a.csv"), (b"[invalid", "a.json"), (b"[]", "a.json"),
                                          (b'{"a":1}\ninvalid', "a.jsonl")])
def test_arquivo_invalido_falha_em_background(ctx, content, name):
    client, iid, _ = ctx
    jid = start(client, iid, content, name)
    assert run(jid)["status"] == "FALHOU"
    assert registros_collection().count_documents({"_importacao_id": jid}) == 0


def test_limites_jsonl_e_cancelar_recebimento(ctx, monkeypatch):
    client, iid, _ = ctx
    assert client.get(base(iid) + "/limites").json()["max_registros"] >= 500000
    monkeypatch.setattr(settings, "importacao_max_registros", 1)
    jid = start(client, iid, b'{"Nome":"Ana"}\n{"Nome":"Maria"}\n', "a.jsonl")
    assert run(jid)["status"] == "FALHOU"
    result = client.post(base(iid), json={"operacao_id": str(uuid.uuid4()), "nome_arquivo": "a.csv", "tamanho_bytes": 5}).json()
    assert client.post(base(iid) + "/" + result["id"] + "/cancelar").json()["status"] == "CANCELADA"


def test_cota_inclui_espera_de_mapeamento_e_cancelar_libera(ctx):
    client, iid, _ = ctx
    jid = start(client, iid, b"Nome\nAna")
    assert run(jid)["status"] == "AGUARDANDO_MAPA"
    for _ in range(4):
        response = client.post(base(iid), json={"operacao_id": str(uuid.uuid4()), "nome_arquivo": "a.csv", "tamanho_bytes": 5})
        assert response.status_code == 201
    payload = {"operacao_id": str(uuid.uuid4()), "nome_arquivo": "a.csv", "tamanho_bytes": 5}
    assert client.post(base(iid), json=payload).status_code == 409
    assert client.post(base(iid) + "/" + jid + "/cancelar").status_code == 200
    assert client.post(base(iid), json=payload).status_code == 201
