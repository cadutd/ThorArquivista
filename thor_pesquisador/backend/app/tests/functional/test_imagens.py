from __future__ import annotations

import uuid
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import event, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import create_app
from app.models.imagem import AuditoriaImagem, ImagemDocumento, RegistroImagem
from app.models.user import Usuario
from app.services import imagem_service, indexacao_service
from app.services.armazenamento_service import armazenamento
from app.services.auth_service import create_session


@pytest.fixture
def context():
    client = TestClient(create_app())
    user = client.post("/api/v1/auth/dev-login").json()
    image_ids = []
    instrument_ids = []
    def instrumento():
        response = client.post("/api/v1/instrumentos", json={"nome": "Fase3 " + uuid.uuid4().hex, "tipo": "CATALOGO"})
        assert response.status_code == 201
        i = response.json()["id"]
        instrument_ids.append(i)
        r = client.post(f"/api/v1/instrumentos/{i}/registros", json={"dados": {}, "status": "ATIVO"})
        assert r.status_code == 201
        return i, r.json()["id"]
    def imagem(direitos="PUBLICO", **extra):
        response = client.post("/api/v1/imagens", json={"titulo": "Fase3 " + uuid.uuid4().hex, "uri": "https://example.org/document.png", "thumbnail_uri": "https://example.org/thumb.png", "direitos_acesso": direitos, **extra})
        assert response.status_code == 201, response.text
        image_ids.append(response.json()["id"])
        return response.json()
    yield client, user, instrumento, imagem, image_ids
    for i in instrument_ids:
        client.delete("/api/v1/instrumentos/" + i)
    for i in image_ids:
        client.delete("/api/v1/imagens/" + i)


def path(i, r):
    return f"/api/v1/instrumentos/{i}/registros/{r}/imagens"


def test_crud_filtros_paginacao_e_iiif(context):
    client, _, _, image, _ = context
    url = image()
    iiif = image(tipo_referencia="IIIF", manifest_iiif_uri="https://example.org/manifest.json")
    repo = image(tipo_referencia="REPOSITORIO_EXTERNO")
    page = client.get("/api/v1/imagens", params={"q": "Fase3", "tipo": "IIIF", "limit": 1, "offset": 0})
    assert page.status_code == 200
    assert len(page.json()["items"]) == 1
    assert iiif["uri"] == iiif["manifest_iiif_uri"]
    assert client.get("/api/v1/imagens", params={"limit": 101}).status_code == 422
    assert client.get("/api/v1/imagens/" + str(uuid.uuid4())).status_code == 404
    changed = client.put("/api/v1/imagens/" + url["id"], json={"titulo": "Atualizado", "uri": url["uri"], "direitos_acesso": "INTERNO"})
    assert changed.status_code == 200
    assert changed.json()["direitos_acesso"] == "INTERNO"
    assert client.delete("/api/v1/imagens/" + repo["id"]).status_code == 204
    assert client.get("/api/v1/imagens/" + repo["id"]).status_code == 404


def test_vinculos_principal_legenda_ordem_e_conflitos(context):
    client, user, instrument, image, _ = context
    i, r = instrument()
    first, second = image(), image()
    for img in [first, second]:
        assert client.post(path(i, r), json={"imagem_id": img["id"], "principal": True}).status_code == 201
    assert client.post(path(i, r), json={"imagem_id": first["id"]}).status_code == 409
    assert client.delete("/api/v1/imagens/" + first["id"]).status_code == 409
    links = client.get(path(i, r)).json()
    assert links["total"] == 2
    assert sum(v["principal"] for v in links["items"]) == 1
    assert client.patch(path(i, r) + "/" + first["id"], json={"legenda": "Legenda", "principal": True}).status_code == 200
    assert client.patch(path(i, r) + "/reordenar", json={"items": [
        {"imagem_id": first["id"], "ordem": 1}, {"imagem_id": second["id"], "ordem": 0}]}).status_code == 204
    assert client.get(path(i, r)).json()["items"][0]["imagem_id"] == second["id"]
    assert client.patch(path(i, r) + "/reordenar", json={"items": [{"imagem_id": first["id"], "ordem": 0}]}).status_code == 409
    assert client.patch(path(i, r) + "/reordenar", json={"items": [
        {"imagem_id": first["id"], "ordem": 2}, {"imagem_id": first["id"], "ordem": 3}]}).status_code == 422
    assert client.post(path(i, "inexistente"), json={"imagem_id": first["id"]}).status_code == 404
    assert client.delete(path(i, r) + "/" + first["id"]).status_code == 204
    with SessionLocal() as db:
        audit = list(db.scalars(select(AuditoriaImagem).where(AuditoriaImagem.imagem_id == uuid.UUID(first["id"]))))
        assert {"CRIACAO", "VINCULO", "ATUALIZACAO_VINCULO", "DESVINCULO"} <= {a.acao for a in audit}
        assert all(str(a.usuario_id) == user["id"] for a in audit)


def test_exclusao_preserva_imagem_compartilhada(context):
    client, user, instrument, image, _ = context
    first_i, first_r = instrument()
    second_i, second_r = instrument()
    img = image()
    for i, r in [(first_i, first_r), (second_i, second_r)]:
        assert client.post(path(i, r), json={"imagem_id": img["id"]}).status_code == 201
    assert client.delete(f"/api/v1/instrumentos/{first_i}/registros/{first_r}").status_code == 200
    assert client.get(path(second_i, second_r)).json()["total"] == 1
    assert client.get("/api/v1/imagens/" + img["id"]).status_code == 200
    assert client.delete("/api/v1/instrumentos/" + second_i).status_code == 200
    assert client.delete("/api/v1/imagens/" + img["id"]).status_code == 204
    with SessionLocal() as db:
        audit = list(db.scalars(select(AuditoriaImagem).where(AuditoriaImagem.imagem_id == uuid.UUID(img["id"]), AuditoriaImagem.acao == "DESVINCULO_EXCLUSAO")))
        assert len(audit) == 2
        assert all(str(a.usuario_id) == user["id"] for a in audit)


def test_acesso_restrito_e_anonimo(context):
    client, _, _, image, _ = context
    restricted = image("RESTRITO")
    internal = image("INTERNO")
    public = image("PUBLICO")
    anonymous = TestClient(create_app())
    assert anonymous.get("/api/v1/imagens").status_code == 401
    assert anonymous.get("/api/v1/imagens/" + restricted["id"] + "/conteudo", follow_redirects=False).status_code == 401
    assert anonymous.get("/api/v1/imagens/" + internal["id"] + "/conteudo", follow_redirects=False).status_code == 401
    assert anonymous.get("/api/v1/imagens/" + public["id"] + "/conteudo", follow_redirects=False).status_code == 307
    with SessionLocal() as db:
        other = Usuario(govbr_sub=uuid.uuid4().hex, nome="Outro usuario")
        db.add(other)
        db.commit()
        token = create_session(db, other)
        other_id = other.id
    other_client = TestClient(create_app())
    other_client.cookies.set(settings.session_cookie_name, token)
    assert other_client.get("/api/v1/imagens/" + restricted["id"]).status_code == 403
    assert other_client.get("/api/v1/imagens/" + internal["id"]).status_code == 403
    from app.models.editorial import AcessoInstrumento
    with SessionLocal() as db:
        db.add(AcessoInstrumento(usuario_id=other_id, papel="CONSULTA_INTERNA"))
        db.commit()
    assert other_client.get("/api/v1/imagens/" + internal["id"]).status_code == 200
    assert other_client.delete("/api/v1/imagens/" + public["id"]).status_code == 403
    assert restricted["id"] not in {i["id"] for i in other_client.get("/api/v1/imagens").json()["items"]}


def test_upload_checksum_miniatura_e_conteudo_protegido(context, monkeypatch):
    client, _, _, _, ids = context
    objects = {}
    monkeypatch.setattr(armazenamento, "salvar_upload", lambda key, data, mime: objects.__setitem__(key, data))
    monkeypatch.setattr(armazenamento, "remover_objeto", lambda key: objects.pop(key, None))
    class Body(BytesIO):
        def iter_chunks(self, chunk_size):
            while data := self.read(chunk_size):
                yield data
    monkeypatch.setattr(armazenamento, "obter_objeto", lambda key: {"Body": Body(objects[key])})
    data = BytesIO()
    Image.new("RGB", (24, 16), "white").save(data, format="PNG")
    raw = data.getvalue()
    created = client.post("/api/v1/imagens/upload", data={"titulo": "Upload", "direitos_acesso": "RESTRITO", "metadados_json": '{"fonte":"teste"}'}, files={"arquivo": ("a.png", raw, "image/png")})
    assert created.status_code == 201, created.text
    img = created.json()
    ids.append(img["id"])
    assert img["checksum_sha256"] == armazenamento.calcular_checksum(raw)
    assert img["largura"] == 24 and img["altura"] == 16
    assert img["metadados_json"]["fonte"] == "teste"
    assert len(objects) == 2
    assert client.get(img["uri"]).content == raw
    assert client.get(img["thumbnail_uri"]).headers["content-type"] == "image/jpeg"
    assert TestClient(create_app()).get(img["uri"]).status_code == 401
    updated = client.put("/api/v1/imagens/" + img["id"], json={"titulo": "Upload editado", "direitos_acesso": "INTERNO"})
    assert updated.status_code == 200, updated.text
    assert client.delete("/api/v1/imagens/" + img["id"]).status_code == 204
    assert not objects


def test_rollback_upload_e_resiliencia_da_fila(context, monkeypatch):
    client, _, instrument, image, _ = context
    removed = []
    def fail_thumb(key, data, mime):
        if mime == "image/jpeg":
            raise HTTPException(503, "S3 indisponivel.")
    monkeypatch.setattr(armazenamento, "salvar_upload", fail_thumb)
    monkeypatch.setattr(armazenamento, "remover_objeto", removed.append)
    raw = BytesIO()
    Image.new("RGB", (2, 2)).save(raw, format="PNG")
    assert client.post("/api/v1/imagens/upload", data={"titulo": "Falha"}, files={"arquivo": ("a.png", raw.getvalue(), "image/png")}).status_code == 503
    assert len(removed) == 1
    def unavailable():
        raise ConnectionError("Redis indisponivel")
    monkeypatch.setattr(indexacao_service, "redis_client", unavailable)
    i, r = instrument()
    img = image()
    assert client.post(path(i, r), json={"imagem_id": img["id"]}).status_code == 201
    assert client.get(path(i, r)).json()["total"] == 1


def test_falha_de_leitura_apos_commit_preserva_upload(context, monkeypatch):
    client, user, _, _, ids = context
    objects = {}
    monkeypatch.setattr(armazenamento, "salvar_upload", lambda key, data, mime: objects.__setitem__(key, data))
    monkeypatch.setattr(armazenamento, "remover_objeto", lambda key: objects.pop(key, None))
    raw = BytesIO()
    Image.new("RGB", (2, 2)).save(raw, format="PNG")
    title = "Upload confirmado " + uuid.uuid4().hex
    with SessionLocal() as db:
        usuario = db.get(Usuario, uuid.UUID(user["id"]))
        def failed_refresh(*args):
            raise RuntimeError("Falha de leitura apos commit")
        monkeypatch.setattr(db, "refresh", failed_refresh)
        with pytest.raises(RuntimeError, match="apos commit"):
            imagem_service.upload(db, title, "INTERNO", None, raw.getvalue(), "image/png", usuario)
    with SessionLocal() as db:
        imagem = db.scalar(select(ImagemDocumento).where(ImagemDocumento.titulo == title))
        assert imagem is not None
        ids.append(str(imagem.id))
        assert imagem.object_key in objects
        assert imagem.thumbnail_key in objects
    assert client.delete("/api/v1/imagens/" + ids[-1]).status_code == 204
    assert not objects


def test_api_busca_preserva_resumo_de_imagens(context, monkeypatch):
    client, _, instrument, image, _ = context
    i, r = instrument()
    public, restricted = image(), image("RESTRITO")
    for img in [public, restricted]:
        assert client.post(path(i, r), json={"imagem_id": img["id"]}).status_code == 201
    doc = indexacao_service.documento_indexavel([], {
        "_id": r, "instrumento_id": i, "dados": {},
        "criado_em": datetime.now(UTC), "atualizado_em": datetime.now(UTC),
    })
    monkeypatch.setattr(indexacao_service, "_meili_request", lambda *args, **kwargs: {"hits": [doc], "estimatedTotalHits": 1})
    response = client.post(f"/api/v1/instrumentos/{i}/buscar-avancado", json={})
    assert response.status_code == 200, response.text
    hit = response.json()["items"][0]
    assert hit["possui_imagens"] is True
    assert hit["total_imagens"] == 2
    assert hit["imagem_principal_thumbnail"] == public["thumbnail_uri"]


def test_resumos_em_lote_nao_expoem_restritas(context):
    client, user, instrument, image, _ = context
    i, r = instrument()
    public, restricted = image(), image("RESTRITO")
    for img in [public, restricted]:
        client.post(path(i, r), json={"imagem_id": img["id"]})
    with SessionLocal() as db:
        statements = []
        callback = lambda *args: statements.append(args[2])
        event.listen(db.bind, "before_cursor_execute", callback)
        try:
            summary = imagem_service.resumos(db, uuid.UUID(i), [r, "outro"])
        finally:
            event.remove(db.bind, "before_cursor_execute", callback)
        assert len(statements) == 1
        assert summary[r]["total_imagens"] == 1
        private = imagem_service.resumos(db, uuid.UUID(i), [r], SimpleNamespace(id=uuid.UUID(user["id"])))
        assert private[r]["total_imagens"] == 2
        documents = indexacao_service._com_imagens(db, uuid.UUID(i), [{"id": r}])
        assert documents[0]["total_imagens"] == 1
