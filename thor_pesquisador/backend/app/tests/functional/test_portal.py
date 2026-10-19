import base64
import time
import uuid
from datetime import UTC, datetime, timedelta
import httpx
import pytest
from jose import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient
from sqlalchemy import func, select, update, event
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.main import create_app
from app.models.user import Sessao, Usuario
from app.models.editorial import AcessoInstrumento, Papel
from app.models.portal import AcessoPortal, ContagemPortal
from app.schemas.portal import DEFAULT_COLORS, CoresPortal
from app.services.auth_service import usuario_from_claims, create_session, Visitante
from app.tests.functional.test_editorial import ctx, publish
from app.tests.functional.test_usuarios import cpf_teste, payload


def visitante():
    cpf = cpf_teste()
    with SessionLocal() as db:
        identity = usuario_from_claims(db, {"sub": cpf})
        assert isinstance(identity, Visitante)
        token = create_session(db, identity)
    client = TestClient(create_app())
    client.cookies.set(settings.session_cookie_name, token)
    return client, cpf, token


def publicado(ctx):
    admin, iid, rid = ctx
    publish(admin, "/api/v1/instrumentos/" + iid)
    publish(admin, "/api/v1/instrumentos/" + iid + "/registros/" + rid)
    return admin, iid, rid


def test_anonimo_apenas_catalogo_sem_conteudo_e_assets_de_registros(ctx):
    admin, iid, rid = publicado(ctx)
    client = TestClient(create_app())
    name = admin.get("/api/v1/instrumentos/" + iid).json()["nome"]
    result = client.get("/api/v1/publico/instrumentos", params={"q": name, "tipo": "CATALOGO", "limit": 100}).json()
    assert iid in [row["id"] for row in result["items"]]
    row = next(row for row in result["items"] if row["id"] == iid)
    assert set(row) == {"id", "nome", "tipo", "descricao", "imagem_card_url"}
    assert "CONFIDENCIAL" not in str(result)
    for suffix in ("", "/buscar", "/facetas", "/registros/" + rid, "/registros/" + rid + "/imagens"):
        response = client.get("/api/v1/publico/instrumentos/" + iid + suffix)
        assert response.status_code == 401, response.text
        assert response.headers["cache-control"] == "private, no-store"
    assert client.post("/api/v1/publico/instrumentos/" + iid + "/buscar", json={}).status_code == 401
    assert client.get("/api/v1/imagens/" + str(uuid.uuid4()) + "/conteudo").status_code == 401
    assert client.get("/api/v1/auth/estado").json() == {"autenticado": False}
    assert client.get("/api/v1/publico/configuracao").status_code == 200
    assert client.get("/api/v1/publico/instrumentos?limit=101").status_code == 422


def test_visitante_sem_cadastro_consulta_mas_nao_administra(ctx):
    _, iid, rid = publicado(ctx)
    with SessionLocal() as db:
        users = db.scalar(select(func.count()).select_from(Usuario))
        grants = db.scalar(select(func.count()).select_from(AcessoInstrumento))
    client, _, _ = visitante()
    assert client.get("/api/v1/auth/me").json()["visitante"]
    assert client.get("/api/v1/auth/me").json()["id"] is None
    assert client.get("/api/v1/auth/estado").json()["area_interna"] is False
    assert client.get("/api/v1/auth/permissoes").json() == {"permissoes": [], "escopos": {}}
    assert client.get("/api/v1/publico/instrumentos/" + iid + "/registros/" + rid).json()["dados"] == {"titulo": "Aprovado"}
    assert client.get("/api/v1/publico/instrumentos/" + iid).json()["campos"][0]["chave"] == "titulo"
    for endpoint in ("/usuarios", "/perfis", "/instrumentos", "/dashboard", "/auditoria",
                     "/exportacoes", "/relatorios", "/retencao/politicas", "/publico/configuracao/administracao"):
        assert client.get("/api/v1" + endpoint).status_code == 403, endpoint
    assert client.put("/api/v1/publico/configuracao/administracao", json={}).status_code == 403
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Usuario)) == users
        assert db.scalar(select(func.count()).select_from(AcessoInstrumento)) == grants


def test_identidade_cadastrada_depois_bloqueio_e_logout(ctx):
    admin, iid, rid = publicado(ctx)
    client, cpf, _ = visitante()
    user = admin.post("/api/v1/usuarios", json=payload(cpf=cpf)).json()
    assert client.get("/api/v1/auth/me").json()["visitante"]
    assert not client.get("/api/v1/auth/permissoes").json()["permissoes"]
    assert admin.post("/api/v1/acessos", json={"usuario_id":user["id"],"papel":"CONSULTA_INTERNA"}).status_code == 201
    assert not client.get("/api/v1/auth/permissoes").json()["permissoes"]
    with SessionLocal() as db:
        fresh_token = create_session(db, usuario_from_claims(db, {"sub":cpf}))
    fresh = TestClient(create_app()); fresh.cookies.set(settings.session_cookie_name, fresh_token)
    assert fresh.get("/api/v1/auth/me").json()["id"] == user["id"]
    assert "dashboard_consultar" in fresh.get("/api/v1/auth/permissoes").json()["permissoes"]
    path = "/api/v1/publico/instrumentos/" + iid + "/registros/" + rid
    assert client.get(path).status_code == 200
    data = admin.get("/api/v1/usuarios/" + user["id"]).json()
    data = {key: data.get(key) for key in ("nome", "username", "cpf", "email", "ativo", "observacoes")}
    assert admin.put("/api/v1/usuarios/" + user["id"], json={**data, "ativo": False}).status_code == 200
    assert client.get(path).status_code == 401
    with SessionLocal() as db:
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            usuario_from_claims(db, {"sub": cpf})
    assert client.get("/api/v1/publico/instrumentos").status_code == 200
    other, _, _ = visitante()
    assert other.post("/api/v1/auth/logout").status_code == 200
    assert other.get(path).status_code == 401


def test_visitante_sessao_expirada_e_revogacao_de_publicacao(ctx):
    admin, iid, rid = publicado(ctx)
    client, _, token = visitante()
    path = "/api/v1/publico/instrumentos/" + iid + "/registros/" + rid
    assert client.get(path).status_code == 200
    from app.tests.functional.test_editorial import command
    assert command(admin, "/api/v1/instrumentos/" + iid, "arquivar")[0].status_code == 200
    assert client.get(path).status_code == 404
    assert iid not in [row["id"] for row in client.get("/api/v1/publico/destaques").json()["items"]]
    from app.services.auth_service import token_hash
    with SessionLocal() as db:
        db.execute(update(Sessao).where(Sessao.token_hash == token_hash(token)).values(expira_em=datetime.now(UTC)-timedelta(seconds=1)))
        db.commit()
    assert client.get(path).status_code == 401


def test_ranking_deduplica_e_custo_constante(ctx, monkeypatch):
    _, iid, _ = publicado(ctx)
    client, _, _ = visitante()
    path = "/api/v1/publico/instrumentos/" + iid + "/acessos"
    for _ in range(3):
        assert client.post(path).status_code == 204
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(AcessoPortal).where(AcessoPortal.instrumento_id == uuid.UUID(iid))) == 1
    second, _, _ = visitante()
    assert second.post(path).status_code == 204
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(AcessoPortal).where(AcessoPortal.instrumento_id == uuid.UUID(iid))) == 2
        assert db.scalar(select(func.sum(ContagemPortal.quantidade)).where(ContagemPortal.instrumento_id == uuid.UUID(iid))) == 2
    _, _, concurrent_token = visitante()
    from concurrent.futures import ThreadPoolExecutor
    def simultaneous(_):
        with TestClient(create_app()) as worker:
            worker.cookies.set(settings.session_cookie_name, concurrent_token)
            return worker.post(path).status_code
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(simultaneous, range(8))) == [204] * 8
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(AcessoPortal).where(AcessoPortal.instrumento_id == uuid.UUID(iid))) == 3
        assert db.scalar(select(func.sum(ContagemPortal.quantidade)).where(ContagemPortal.instrumento_id == uuid.UUID(iid))) == 3
    statements = []
    def capture(conn, cursor, statement, *args):
        statements.append(statement)
    event.listen(engine, "before_cursor_execute", capture)
    try:
        result = TestClient(create_app()).get("/api/v1/publico/destaques?limit=6").json()
    finally:
        event.remove(engine, "before_cursor_execute", capture)
    assert result["com_acessos"] and len(result["items"]) <= 6
    assert all("sessao_chave" not in row and "total" not in row for row in result["items"])
    assert len([s for s in statements if "SELECT" in s.upper()]) <= 2
    class Future(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2099, 1, 1, tzinfo=UTC)
    monkeypatch.setattr("app.services.portal_service.datetime", Future)
    fallback = TestClient(create_app()).get("/api/v1/publico/destaques?limit=6").json()
    assert not fallback["com_acessos"] and 0 < len(fallback["items"]) <= 6


def test_configuracao_validacao_escopo_concorrencia_e_auditoria(ctx):
    admin, iid, _ = ctx
    path = "/api/v1/publico/configuracao/administracao"
    original = admin.get(path).json()
    changed = {**original, "nome_instituicao": "Arquivo Institucional"}
    try:
        saved = admin.put(path, json=changed)
        assert saved.status_code == 200, saved.text
        assert admin.put(path, json=changed).status_code == 409
        public = TestClient(create_app()).get("/api/v1/publico/configuracao").json()
        assert public["nome_instituicao"] == changed["nome_instituicao"]
        assert set(public) == {"nome_instituicao", "cores", "versao"}
        for colors in ({**DEFAULT_COLORS, "primaria": "url(javascript:alert(1))"},
                       {**DEFAULT_COLORS, "texto": "#ffffff"},
                       {**DEFAULT_COLORS, "destaque": "#eeeeee"},
                       {**DEFAULT_COLORS, "surpresa": "red"}):
            assert admin.put(path, json={**public, "cores": colors}).status_code == 422
        visitor, _, _ = visitante()
        assert visitor.put(path, json=public).status_code == 403
        from app.models.conformidade import AuditoriaGeral
        with SessionLocal() as db:
            row = db.scalar(select(AuditoriaGeral).where(AuditoriaGeral.acao == "EDITAR_CONFIGURACAO_PORTAL").order_by(AuditoriaGeral.criado_em.desc()))
            assert row.usuario_id and row.agente != "sistema"
            role = Papel(nome="PORTAL_"+uuid.uuid4().hex, permissoes=["portal_configuracao_consultar", "portal_configuracao_editar"])
            user = Usuario(nome="Configurador restrito")
            db.add_all([role, user]); db.flush()
            db.add(AcessoInstrumento(usuario_id=user.id, papel=role.nome, instrumento_id=uuid.UUID(iid)))
            db.commit()
            token = create_session(db, user)
        scoped = TestClient(create_app()); scoped.cookies.set(settings.session_cookie_name, token)
        assert scoped.get(path).status_code == 403
        assert scoped.put(path, json=public).status_code == 403
    finally:
        latest = admin.get(path).json()
        assert admin.put(path, json={**original, "versao": latest["versao"]}).status_code == 200


@pytest.mark.parametrize("failure", [None, "nonce", "issuer", "signature", "expired", "audience"])
def test_callback_oidc_real_sem_usuario(monkeypatch, failure):
    from app.api.v1 import auth
    from urllib.parse import urlsplit
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    numbers = key.public_key().public_numbers()
    encode = lambda n: base64.urlsafe_b64encode(n.to_bytes((n.bit_length()+7)//8, "big")).decode().rstrip("=")
    jwks = {"keys": [{"kid": "test-key", "kty": "RSA", "alg": "RS256", "use": "sig", "n": encode(numbers.n), "e": encode(numbers.e)}]}
    cpf = cpf_teste()
    now = int(time.time())
    provider = urlsplit(settings.govbr_authorize_url)
    claims = {"sub": cpf, "nonce": "wrong" if failure=="nonce" else "test-nonce",
              "iss": "https://wrong.example" if failure=="issuer" else provider.scheme+"://"+provider.netloc,
              "aud": "wrong" if failure=="audience" else settings.govbr_client_id,
              "iat": now, "exp": now-10 if failure=="expired" else now+300}
    token = jwt.encode(claims, pem, algorithm="RS256", headers={"kid":"test-key"})
    if failure == "signature":
        segments = token.split("."); segments[2] = ("a" if segments[2][0] != "a" else "b") + segments[2][1:]; token = ".".join(segments)
    def provider_response(request):
        if request.url == settings.govbr_token_url:
            assert b"code_verifier=test-verifier" in request.content
            return httpx.Response(200, json={"id_token":token})
        assert request.url == settings.govbr_jwks_url
        return httpx.Response(200, json=jwks)
    original_client = httpx.AsyncClient
    monkeypatch.setattr(auth, "exchange_code_for_claims", auth.exchange_code_for_claims)
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(provider_response), **kwargs))
    client = TestClient(create_app())
    for name, value in {"thor_auth_state":"test-state", "thor_auth_nonce":"test-nonce",
                        "thor_auth_verifier":"test-verifier", "thor_auth_return_to":"/consulta"}.items():
        client.cookies.set(name, value)
    result = client.get("/api/v1/auth/govbr/callback?code=controlled-code&state=test-state", follow_redirects=False)
    if failure:
        assert result.status_code == 401, result.text
        assert client.get("/api/v1/auth/me").status_code == 401
    else:
        assert result.status_code == 307 and result.headers["location"].endswith("/consulta")
        assert client.get("/api/v1/auth/me").json()["visitante"]
        with SessionLocal() as db:
            assert db.scalar(select(Usuario).where(Usuario.cpf == cpf)) is None


def test_csrf_cache_rate_e_readiness(ctx, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("app.core.security.monotonic", lambda: clock[0])
    client = TestClient(create_app())
    assert client.post("/api/v1/auth/dev-login", headers={"Origin":"https://outside.example"}).status_code == 403
    assert client.post("/api/v1/auth/dev-login", headers={"Sec-Fetch-Site":"cross-site"}).status_code == 403
    assert client.get("/api/v1/publico/configuracao").headers["x-content-type-options"] == "nosniff"
    for _ in range(30):
        assert client.get("/api/v1/auth/govbr/start").status_code == 200
    assert client.get("/api/v1/auth/govbr/start").status_code == 429
    clock[0] += 61
    assert client.get("/api/v1/auth/govbr/start").status_code == 200
    assert client.get("/api/v1/ready").status_code == 200
    def unavailable(*a, **kw):
        raise RuntimeError("Sensitive dependency details")
    monkeypatch.setattr("app.api.v1.health.get_mongo_client", unavailable)
    response = client.get("/api/v1/ready")
    assert response.status_code == 503 and "Sensitive" not in response.text
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/operacao/metricas").status_code == 401
    assert ctx[0].get("/api/v1/operacao/metricas").status_code == 200


def test_visitante_conteudo_somente_de_imagem_publicada_e_direitos_atuais(ctx):
    admin, iid, rid = ctx
    path = "/api/v1/instrumentos/" + iid
    image = admin.post("/api/v1/imagens", json={"titulo": "Imagem publicada",
        "uri": "https://example.org/publicada.png", "direitos_acesso": "PUBLICO"}).json()
    content = "/api/v1/imagens/" + image["id"] + "/conteudo"
    visitor, _, _ = visitante()
    assert visitor.get(content, follow_redirects=False).status_code == 404
    assert admin.post(path + "/registros/" + rid + "/imagens", json={"imagem_id": image["id"]}).status_code == 201
    publish(admin, path)
    publish(admin, path + "/registros/" + rid)
    response = visitor.get(content, follow_redirects=False)
    assert response.status_code == 307 and response.headers["location"] == image["uri"]
    assert admin.put("/api/v1/imagens/" + image["id"], json={"titulo": image["titulo"],
        "uri": image["uri"], "direitos_acesso": "RESTRITO"}).status_code == 200
    assert visitor.get(content, follow_redirects=False).status_code in (403, 404)
    assert TestClient(create_app()).get(content, follow_redirects=False).status_code == 401
