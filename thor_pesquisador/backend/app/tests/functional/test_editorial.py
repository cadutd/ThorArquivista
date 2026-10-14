import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import create_app
from app.core.config import settings
from app.db.mongo import registros_collection, snapshots_collection
from app.db.session import SessionLocal
from app.models.editorial import AcessoInstrumento, EditorialRegistro
from app.models.instrumento import Instrumento, IndexacaoJob
from app.models.user import Usuario
from app.services.auth_service import create_session
from app.services import editorial_service, publicacao_service


@pytest.fixture
def ctx(monkeypatch):
    from app.services import registro_service, instrumento_service
    monkeypatch.setattr(registro_service, "enqueue_registro", lambda *a, **kw: None)
    monkeypatch.setattr(instrumento_service, "enqueue_indexacao", lambda *a, **kw: None)
    client = TestClient(create_app())
    assert client.post("/api/v1/auth/dev-login").status_code == 200
    response = client.post("/api/v1/instrumentos", json={"nome": "Editorial " + uuid.uuid4().hex,
        "tipo": "CATALOGO", "visibilidade": "PUBLICO"})
    assert response.status_code == 201, response.text
    i = response.json()["id"]
    base = "/api/v1/instrumentos/" + i
    for key, public in [("titulo", True), ("segredo", False)]:
        field = client.post(base + "/campos", json={"nome": key, "chave": key,
            "tipo": "TEXTO_CURTO", "exibir_publico": public, "facetavel": public})
        assert field.status_code == 201, field.text
    response = client.post(base + "/registros", json={"dados": {"titulo": "Aprovado", "segredo": "CONFIDENCIAL"}})
    assert response.status_code == 201, response.text
    return client, i, response.json()["id"]


def command(client, path, action, **overrides):
    current = client.get(path).json()
    payload = {"operacao_id": str(uuid.uuid4()), "versao": current.get("versao", current.get("versao_editorial")),
               "justificativa": "Teste auditavel"}
    payload.update(overrides)
    return client.post(path + "/editorial/" + action, json=payload), payload


def publish(client, path):
    for action in ["enviar-revisao", "aprovar", "publicar"]:
        response, _ = command(client, path, action)
        assert response.status_code == 200, response.text


def test_publicacao_imutavel_idempotencia_e_revisao(ctx):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    path = base + "/registros/" + r
    assert client.get("/api/v1/publico/instrumentos/" + i).status_code == 404
    assert client.put(base, json={"status": "PUBLICADO"}).status_code == 409
    publish(client, base)
    assert client.get("/api/v1/publico/instrumentos/" + i + "/registros/" + r).status_code == 404
    command(client, path, "enviar-revisao")
    command(client, path, "aprovar")
    response, payload = command(client, path, "publicar")
    assert response.status_code == 200, response.text
    retry = client.post(path + "/editorial/publicar", json=payload)
    assert retry.json() == response.json()
    payload["justificativa"] = "Outro comando"
    assert client.post(path + "/editorial/publicar", json=payload).status_code == 409
    public_path = "/api/v1/publico/instrumentos/" + i + "/registros/" + r
    assert client.get(public_path).json()["dados"] == {"titulo": "Aprovado"}
    current = client.get(path).json()
    assert current["status_editorial"] == "PUBLICADO"
    assert client.put(path, json={"dados": {"titulo": "Alterado"}}).status_code == 409
    assert client.put(path, json={"dados": {"titulo": "Rascunho", "segredo": "PRIVADO"}, "versao": current["versao"]}).status_code == 200
    assert client.get(path).json()["status_editorial"] == "RASCUNHO"
    assert client.get(public_path).json()["dados"] == {"titulo": "Aprovado"}
    assert client.put(path, json={"dados": {}, "versao": current["versao"]}).status_code == 409
    assert client.delete(base).status_code == 409
    publish(client, path)
    assert client.get(public_path).json()["dados"] == {"titulo": "Rascunho"}
    response, _ = command(client, path, "arquivar")
    assert response.status_code == 200
    assert client.get(public_path).status_code == 404
    response, _ = command(client, path, "reabrir")
    assert response.status_code == 200
    assert client.get(public_path).status_code == 404
    assert len(client.get(path + "/versoes").json()["items"]) == 2


@pytest.mark.parametrize("status", ["INATIVO", "EXCLUIDO"])
def test_estados_operacionais_nao_publicam(ctx, status):
    client, i, r = ctx
    path = "/api/v1/instrumentos/" + i + "/registros/" + r
    assert client.put(path, json={"dados": {"titulo": "Privado"}, "status": status}).status_code == 200
    response, _ = command(client, path, "enviar-revisao")
    assert response.status_code == 409
    assert client.get("/api/v1/publico/instrumentos/" + i + "/registros/" + r).status_code == 404


@pytest.mark.parametrize("role,allowed", [
    ("GESTOR_INSTRUMENTOS", {"enviar-revisao", "publicar", "arquivar"}),
    ("EDITOR", {"enviar-revisao"}),
    ("REVISOR", {"aprovar", "devolver"}),
    ("CONSULTA_INTERNA", set()), ("PUBLICO_AUTENTICADO", set()),
])
def test_permissoes_por_papel_e_escopo(ctx, role, allowed):
    admin, i, r = ctx
    with SessionLocal() as db:
        user = Usuario(govbr_sub=uuid.uuid4().hex, nome="Usuario " + role)
        db.add(user); db.flush()
        db.add(AcessoInstrumento(usuario_id=user.id, papel=role, instrumento_id=uuid.UUID(i)))
        db.commit()
        token = create_session(db, user)
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    base = "/api/v1/instrumentos/" + i
    assert client.get(base).status_code == (403 if role == "PUBLICO_AUTENTICADO" else 200)
    for action in ["enviar-revisao", "aprovar", "devolver", "publicar", "arquivar"]:
        response = client.post(base + "/registros/" + r + "/editorial/" + action,
            json={"operacao_id": str(uuid.uuid4()), "versao": 1, "justificativa": "Teste"})
        assert (response.status_code != 403) == (action in allowed), (role, action, response.text)
    other = admin.post("/api/v1/instrumentos", json={"nome": "Outro", "tipo": "CATALOGO"}).json()["id"]
    assert client.get("/api/v1/instrumentos/" + other).status_code == 403
    assert all(item["id"] == i for item in client.get("/api/v1/instrumentos").json()["items"])
    for endpoint in ["buscar-avancado", "reindexar"]:
        assert client.post("/api/v1/instrumentos/" + other + "/" + endpoint, json={}).status_code == 403
    assert client.get("/api/v1/instrumentos/" + other + "/facetas").status_code == 403


def test_crud_acessos_e_protecao_do_proprio_admin(ctx):
    admin, instrument_id, _ = ctx
    with SessionLocal() as db:
        user = Usuario(govbr_sub="acesso_" + uuid.uuid4().hex, nome="Usuario dos acessos")
        db.add(user); db.commit()
        user_id = str(user.id)
        token = create_session(db, user)
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    payload = {"usuario_id": user_id, "instrumento_id": instrument_id, "papel": "EDITOR"}
    assert client.get("/api/v1/acessos").status_code == 403
    response = admin.post("/api/v1/acessos", json=payload)
    assert response.status_code == 201
    path = "/api/v1/acessos/" + response.json()["id"]
    assert admin.post("/api/v1/acessos", json=payload).status_code == 409
    assert admin.get(path).json()["papel"] == "EDITOR"
    listing = admin.get("/api/v1/acessos?q=Usuario dos acessos&papel=EDITOR&limit=1").json()
    assert listing["total"] == 1 and len(listing["items"]) == 1
    assert admin.get("/api/v1/acessos?q=Usuario dos acessos&offset=1").json()["items"] == []
    assert client.get("/api/v1/instrumentos/" + instrument_id).status_code == 200
    assert admin.put(path, json={**payload, "papel": "PUBLICO_AUTENTICADO"}).status_code == 200
    assert client.get("/api/v1/instrumentos/" + instrument_id).status_code == 403
    assert admin.put(path, json={**payload, "papel": "ADMIN"}).status_code == 422
    assert admin.delete(path).status_code == 200
    assert admin.get(path).status_code == 404
    self_id = admin.get("/api/v1/auth/me").json()["id"]
    own = next(a for a in admin.get("/api/v1/acessos?papel=ADMIN").json()["items"] if a["usuario_id"] == self_id)
    assert admin.delete("/api/v1/acessos/" + own["id"]).status_code == 409
    assert admin.put("/api/v1/acessos/" + own["id"], json={
        "usuario_id": self_id, "papel": "EDITOR", "instrumento_id": None}).status_code == 409


def test_admin_lista_imagem_restrita_sem_ampliar_acesso_interno(ctx):
    admin, instrument_id, _ = ctx
    with SessionLocal() as db:
        user = Usuario(govbr_sub="imagem_" + uuid.uuid4().hex, nome="Editor da imagem")
        db.add(user); db.commit()
        db.add(AcessoInstrumento(usuario_id=user.id, instrumento_id=uuid.UUID(instrument_id), papel="EDITOR"))
        db.commit()
        token = create_session(db, user)
    creator = TestClient(create_app())
    creator.cookies.set(settings.session_cookie_name, token)
    response = creator.post("/api/v1/imagens", json={"titulo": "Restrita ao criador",
        "uri": "https://example.org/restrita.png", "direitos_acesso": "RESTRITO"})
    assert response.status_code == 201
    image = response.json()
    assert any(i["id"] == image["id"] for i in admin.get("/api/v1/imagens?direitos=RESTRITO").json()["items"])
    assert admin.get("/api/v1/imagens/" + image["id"]).status_code == 200
    with SessionLocal() as db:
        reader = Usuario(govbr_sub="reader_" + uuid.uuid4().hex, nome="Consulta da imagem")
        db.add(reader); db.commit()
        db.add(AcessoInstrumento(usuario_id=reader.id, papel="CONSULTA_INTERNA"))
        db.commit()
        token = create_session(db, reader)
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    assert all(i["id"] != image["id"] for i in client.get("/api/v1/imagens").json()["items"])
    assert client.get("/api/v1/imagens/" + image["id"]).status_code == 403


def test_falha_snapshot_nao_publica(ctx, monkeypatch):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    path = base + "/registros/" + r
    publish(client, base)
    command(client, path, "enviar-revisao"); command(client, path, "aprovar")
    class FailingSnapshots:
        def update_one(self, *args, **kwargs):
            raise RuntimeError("Mongo indisponivel")
    monkeypatch.setattr(editorial_service, "snapshots_collection", lambda: FailingSnapshots())
    with pytest.raises(RuntimeError):
        command(client, path, "publicar")
    assert client.get(path).json()["status_editorial"] == "APROVADO"
    assert client.get("/api/v1/publico/instrumentos/" + i + "/registros/" + r).status_code == 404


def test_indice_publico_real_e_revogacao(ctx):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    publish(client, base); publish(client, base + "/registros/" + r)
    with SessionLocal() as db:
        for _ in range(30):
            job = db.scalar(select(IndexacaoJob).where(IndexacaoJob.instrumento_id == uuid.UUID(i),
                IndexacaoJob.tipo == "PUBLICACAO", IndexacaoJob.status == "PENDENTE").limit(1))
            if not job:
                break
            publicacao_service.processar_pendente(db, batch_size=1, instrumento_id=uuid.UUID(i))
        instrument = db.get(Instrumento, uuid.UUID(i))
        assert instrument.geracao_indexada == instrument.geracao_publica
    public = "/api/v1/publico/instrumentos/" + i
    response = client.get(public + "/buscar", params={"q": "Aprovado"})
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert "CONFIDENCIAL" not in response.text
    assert client.get(public + "/buscar", params={"q": "CONFIDENCIAL"}).json()["total"] == 0
    assert client.put(base, json={"visibilidade": "INTERNO", "versao_editorial": client.get(base).json()["versao_editorial"]}).status_code == 200
    for suffix in ["", "/buscar", "/facetas", "/registros/" + r]:
        assert client.get(public + suffix).status_code == 404


def test_geracao_defasada_nao_expoe_totais(ctx):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    publish(client, base); publish(client, base + "/registros/" + r)
    assert client.get("/api/v1/publico/instrumentos/" + i + "/buscar").status_code == 503
    assert client.get("/api/v1/publico/instrumentos/" + i + "/facetas").status_code == 503


def test_snapshot_orfao_sql_falha_e_retentativa(ctx, monkeypatch):
    from sqlalchemy.orm import Session
    from app.models.editorial import EventoEditorial
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    path = base + "/registros/" + r
    publish(client, base)
    command(client, path, "enviar-revisao"); command(client, path, "aprovar")
    original = Session.commit
    failed = False
    def fail_once(db):
        nonlocal failed
        if not failed and any(isinstance(o, EventoEditorial) and o.acao == "publicar" for o in db.new):
            failed = True
            raise RuntimeError("Falha SQL simulada")
        return original(db)
    monkeypatch.setattr(Session, "commit", fail_once)
    payload = {"operacao_id": str(uuid.uuid4()), "versao": client.get(path).json()["versao"]}
    with pytest.raises(RuntimeError):
        client.post(path + "/editorial/publicar", json=payload)
    assert snapshots_collection().find_one({"_id": payload["operacao_id"]})
    public = "/api/v1/publico/instrumentos/" + i + "/registros/" + r
    assert client.get(public).status_code == 404
    retry = client.post(path + "/editorial/publicar", json=payload)
    assert retry.status_code == 200, retry.text
    assert client.get(public).json()["dados"] == {"titulo": "Aprovado"}


def test_revogacao_persiste_quando_mongo_falha(ctx, monkeypatch):
    from app.services import registro_service
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    path = base + "/registros/" + r
    publish(client, base); publish(client, path)
    collection = registros_collection()
    class FailingCollection:
        def find_one(self, *args, **kwargs):
            return collection.find_one(*args, **kwargs)
        def find_one_and_update(self, *args, **kwargs):
            raise RuntimeError("Falha Mongo simulada")
    monkeypatch.setattr(registro_service, "_collection", lambda *_: FailingCollection())
    payload = {"dados": {"titulo": "Privado"}, "status": "INATIVO", "versao": client.get(path).json()["versao"]}
    with pytest.raises(RuntimeError):
        client.put(path, json=payload)
    assert client.get("/api/v1/publico/instrumentos/" + i + "/registros/" + r).status_code == 404
    assert client.get("/api/v1/publico/instrumentos/" + i + "/buscar").status_code == 503


def test_galeria_snapshot_revogacao_e_historico(ctx):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    path = base + "/registros/" + r
    image = client.post("/api/v1/imagens", json={"titulo": "Imagem aprovada",
        "uri": "https://example.org/image.png", "direitos_acesso": "PUBLICO"}).json()
    assert client.post(path + "/imagens", json={"imagem_id": image["id"]}).status_code == 201
    publish(client, base); publish(client, path)
    public = "/api/v1/publico/instrumentos/" + i + "/registros/" + r + "/imagens"
    assert client.get(public).json()["total"] == 1
    assert client.delete(path + "/imagens/" + image["id"]).status_code == 409
    assert client.put(path, json={"dados": {"titulo": "Draft"}, "versao": client.get(path).json()["versao"]}).status_code == 200
    assert client.delete(path + "/imagens/" + image["id"]).status_code == 204
    assert client.get(public).json()["total"] == 1
    assert client.delete("/api/v1/imagens/" + image["id"]).status_code == 409
    assert client.put("/api/v1/imagens/" + image["id"], json={"titulo": "Revogada",
        "uri": image["uri"], "direitos_acesso": "INTERNO"}).status_code == 200
    assert client.get(public).json()["total"] == 0


def test_duas_transicoes_concorrentes(ctx):
    from concurrent.futures import ThreadPoolExecutor
    client, i, r = ctx
    path = "/api/v1/instrumentos/" + i + "/registros/" + r
    version = client.get(path).json()["versao"]
    def submit():
        c = TestClient(create_app())
        c.cookies.update(client.cookies)
        return c.post(path + "/editorial/enviar-revisao", json={"operacao_id": str(uuid.uuid4()), "versao": version}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: submit(), range(2)))
    assert sorted(results) == [200, 409]


def test_job_em_lotes_falha_e_retoma(ctx, monkeypatch):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    publish(client, base)
    publish(client, base + "/registros/" + r)
    for n in range(2):
        record = client.post(base + "/registros", json={"dados": {"titulo": f"Pagina {n}"}}).json()
        publish(client, base + "/registros/" + record["id"])
    with SessionLocal() as db:
        instrument = db.get(Instrumento, uuid.UUID(i))
        while db.scalar(select(IndexacaoJob.id).where(IndexacaoJob.instrumento_id == instrument.id,
            IndexacaoJob.geracao_publica != instrument.geracao_publica, IndexacaoJob.status == "PENDENTE").limit(1)):
            publicacao_service.processar_pendente(db, batch_size=1, instrumento_id=instrument.id)
        assert publicacao_service.processar_pendente(db, batch_size=1, instrumento_id=instrument.id)
        job = db.scalar(select(IndexacaoJob).where(IndexacaoJob.instrumento_id == instrument.id,
            IndexacaoJob.geracao_publica == instrument.geracao_publica))
        assert job.processados == 1
        cursor = job.ultimo_cursor_mongodb
        original = publicacao_service._meili_request
        def fail(method, path, *args, **kwargs):
            if path.endswith("/documents"):
                raise RuntimeError("Falha de projecao simulada")
            return original(method, path, *args, **kwargs)
        with monkeypatch.context() as m:
            m.setattr(publicacao_service, "_meili_request", fail)
            publicacao_service.processar_pendente(db, batch_size=1, instrumento_id=instrument.id)
        db.refresh(job)
        assert job.status == "FALHOU" and job.ultimo_cursor_mongodb == cursor
        assert client.get("/api/v1/publico/instrumentos/" + i + "/buscar").status_code == 503
        job.status = "PENDENTE"; db.commit()
        for _ in range(4):
            publicacao_service.processar_pendente(db, batch_size=1, instrumento_id=instrument.id)
        db.refresh(job)
        assert job.status == "CONCLUIDO" and job.processados == 3
    assert client.get("/api/v1/publico/instrumentos/" + i + "/buscar").json()["total"] == 3


@pytest.mark.parametrize("status", ["ATIVO", "INATIVO", "EXCLUIDO"])
def test_backfill_legado_preserva_operacao_sem_publicar(ctx, status):
    from datetime import UTC, datetime
    from app.editorial_cli import backfill
    client, i, _ = ctx
    record_id = "zz_backfill_" + uuid.uuid4().hex
    registros_collection().insert_one({"_id": record_id, "instrumento_id": i, "schema_version": 1,
        "dados": {"titulo": "Legado"}, "status": status, "criado_em": datetime.now(UTC), "atualizado_em": datetime.now(UTC)})
    with SessionLocal() as db:
        instrument = db.get(Instrumento, uuid.UUID(i))
        instrument.status = "PUBLICADO"; db.commit()
        assert backfill(db, after="zz_backfill_", limit=1000, instrumento_id=uuid.UUID(i))
        backfill(db, after="zz_backfill_", limit=1000, instrumento_id=uuid.UUID(i))
        row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == record_id))
        assert row.status_operacional == status and row.status_editorial == "RASCUNHO" and row.snapshot_id is None
    assert registros_collection().find_one({"_id": record_id})["status"] == status
    assert client.get("/api/v1/publico/instrumentos/" + i).status_code == 404


def test_backfill_por_instrumento_preserva_orfaos(ctx):
    from datetime import UTC, datetime
    from app.editorial_cli import backfill
    _, instrument_id, _ = ctx
    orphan_id = "zz_orfao_" + uuid.uuid4().hex
    legacy_id = "zz_legado_" + uuid.uuid4().hex
    now = datetime.now(UTC)
    orphan = {"_id": orphan_id, "instrumento_id": str(uuid.uuid4()),
        "dados": {"titulo": "Orfao preservado"}, "status": "ATIVO",
        "criado_em": now, "atualizado_em": now}
    registros_collection().insert_one(orphan.copy())
    registros_collection().insert_one({**orphan, "_id": legacy_id, "instrumento_id": instrument_id})
    before = registros_collection().find_one({"_id": orphan_id})
    with SessionLocal() as db:
        assert backfill(db, after="zz_", instrumento_id=uuid.UUID(instrument_id)) == legacy_id
        assert backfill(db, after=legacy_id, instrumento_id=uuid.UUID(instrument_id)) is None
        row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == legacy_id))
        assert row.status_editorial == "RASCUNHO" and row.snapshot_id is None
        assert db.scalar(select(EditorialRegistro).where(EditorialRegistro.registro_id == orphan_id)) is None
    assert registros_collection().find_one({"_id": orphan_id}) == before
    registros_collection().delete_one({"_id": orphan_id})


def test_alteracao_de_campo_invalida_aprovacao_e_revoga(ctx):
    client, i, r = ctx
    base = "/api/v1/instrumentos/" + i
    path = base + "/registros/" + r
    publish(client, base)
    command(client, path, "enviar-revisao"); command(client, path, "aprovar")
    field = next(f for f in client.get(base + "/campos").json() if f["chave"] == "titulo")
    assert client.put(base + "/campos/" + field["id"], json={"exibir_publico": False}).status_code == 200
    response, _ = command(client, path, "publicar")
    assert response.status_code == 409
    assert client.get("/api/v1/publico/instrumentos/" + i).json()["campos"] == []
