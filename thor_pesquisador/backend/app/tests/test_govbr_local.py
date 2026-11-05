import asyncio
import base64
from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlsplit
import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from app.core.config import Settings, settings
from app.main import create_app
from app.services import auth_service
from app.tests.test_govbr_token import signed


CALLBACK = "https://localhost:8443/api/v1/auth/govbr/callback"


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, "govbr_client_id", "cliente-teste")
    monkeypatch.setattr(settings, "govbr_client_secret", SecretStr("segredo-sintetico"))
    monkeypatch.setattr(settings, "govbr_redirect_uri", CALLBACK)
    monkeypatch.setattr(settings, "public_app_url", "https://localhost:8443")
    monkeypatch.setattr(settings, "session_cookie_secure", True)


def transport(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(
        transport=httpx.MockTransport(handler), **kw))


def test_docker_secret_mascarado_e_prioridade_sobre_env(tmp_path):
    path = tmp_path / "secret"
    path.write_text("segredo-do-arquivo\n", encoding="utf-8")
    config = Settings(_env_file=None, govbr_client_secret="ignorado",
                      govbr_client_secret_file=str(path))
    assert config.govbr_client_secret.get_secret_value() == "segredo-do-arquivo"
    assert "segredo-do-arquivo" not in repr(config)
    assert "segredo-do-arquivo" not in config.model_dump_json()


@pytest.mark.parametrize("content", ["", "  ", "change-me", "x" * 8193])
def test_recusa_arquivo_de_segredo_invalido(tmp_path, content):
    path = tmp_path / "secret"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, govbr_client_secret_file=str(path))


def test_recusa_arquivo_de_segredo_ausente(tmp_path):
    with pytest.raises(ValidationError, match="indisponivel"):
        Settings(_env_file=None, govbr_client_secret_file=str(tmp_path / "ausente"))


def test_start_https_retorno_pkce_cookies_e_segredo(configured):
    client = TestClient(create_app(), base_url="https://localhost:8443")
    response = client.get("/api/v1/auth/govbr/start", params={"next": "/consulta/registro-teste"})
    assert response.status_code == 200
    query = parse_qs(urlsplit(response.json()["authorization_url"]).query)
    assert query["redirect_uri"] == [CALLBACK]
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["cliente-teste"]
    assert query["scope"] == ["openid email profile"]
    assert query["code_challenge_method"] == ["S256"]
    verifier = client.cookies["thor_auth_verifier"]
    assert 43 <= len(verifier) <= 128
    assert query["code_challenge"] == [auth_service.code_challenge(verifier)]
    assert query["state"] == [client.cookies["thor_auth_state"]]
    assert query["nonce"] == [client.cookies["thor_auth_nonce"]]
    cookie = SimpleCookie()
    cookie.load("thor_auth_return_to=" + client.cookies["thor_auth_return_to"])
    assert cookie["thor_auth_return_to"].value == "/consulta/registro-teste"
    assert "segredo-sintetico" not in response.text
    assert "client_secret" not in query
    for value in response.headers.get_list("set-cookie"):
        assert "HttpOnly" in value and "Secure" in value and "SameSite=lax" in value


def test_troca_codigo_basic_pkce_callback_e_assinatura(configured, signed, monkeypatch):
    token, jwks = signed
    requests = []
    def provider(request):
        requests.append(request)
        if str(request.url) == settings.govbr_token_url:
            assert parse_qs(request.content.decode()) == {
                "grant_type": ["authorization_code"], "code": ["codigo-sintetico"],
                "redirect_uri": [CALLBACK], "code_verifier": ["verificador-sintetico"]}
            expected = base64.b64encode(b"cliente-teste:segredo-sintetico").decode()
            assert request.headers["authorization"] == "Basic " + expected
            return httpx.Response(200, json={"id_token": token()})
        assert str(request.url) == settings.govbr_jwks_url
        return httpx.Response(200, json=jwks)
    transport(monkeypatch, provider)
    claims = asyncio.run(auth_service.exchange_code_for_claims("codigo-sintetico", "verificador-sintetico"))
    assert claims["sub"] == "52998224725"
    assert len(requests) == 2


def test_fluxo_https_callback_sessao_consultiva(configured, signed, monkeypatch):
    assert settings.database_url.rsplit("/", 1)[-1].endswith("_test")
    assert settings.mongodb_database.endswith("_test")
    from app.tests.functional.test_usuarios import cpf_teste
    token, jwks = signed
    client = TestClient(create_app(), base_url="https://localhost:8443")
    response = client.get("/api/v1/auth/govbr/start", params={"next": "/consulta/registro-teste"})
    query = parse_qs(urlsplit(response.json()["authorization_url"]).query)
    cpf = cpf_teste()
    def provider(request):
        if str(request.url) == settings.govbr_token_url:
            return httpx.Response(200, json={"id_token": token({"sub": cpf, "nonce": query["nonce"][0]})})
        return httpx.Response(200, json=jwks)
    transport(monkeypatch, provider)
    response = client.get("/api/v1/auth/govbr/callback", params={
        "state": query["state"][0], "code": "codigo-sintetico"}, follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://localhost:8443/consulta/registro-teste"
    assert any(settings.session_cookie_name in value and "Secure" in value and "HttpOnly" in value
               for value in response.headers.get_list("set-cookie"))
    assert client.get("/api/v1/auth/me").json()["visitante"]
    assert client.get("/api/v1/auth/permissoes").json() == {"permissoes": [], "escopos": {}}
    assert "thor_auth_verifier" not in client.cookies


@pytest.mark.parametrize("upstream,expected", [(400,401),(401,401),(403,401),(429,502),(500,502)])
def test_erro_do_provedor_nao_expoe_corpo_url_ou_segredos(configured, monkeypatch, upstream, expected):
    transport(monkeypatch, lambda request: httpx.Response(upstream, text="codigo-privado segredo-sintetico"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(auth_service.exchange_code_for_claims("codigo-privado", "verificador"))
    assert error.value.status_code == expected
    assert "codigo-privado" not in error.value.detail and "segredo-sintetico" not in error.value.detail


def test_timeout_sem_detalhes_da_requisicao(configured, monkeypatch):
    def provider(request):
        raise httpx.ConnectTimeout("codigo-privado", request=request)
    transport(monkeypatch, provider)
    with pytest.raises(HTTPException) as error:
        asyncio.run(auth_service.exchange_code_for_claims("codigo", "verificador"))
    assert error.value.status_code == 502 and "codigo-privado" not in error.value.detail


def test_resposta_invalida_sem_dados_sensiveis(configured, monkeypatch):
    transport(monkeypatch, lambda request: httpx.Response(200, text="nao-e-json codigo-privado"))
    with pytest.raises(HTTPException) as error:
        asyncio.run(auth_service.exchange_code_for_claims("codigo", "verificador"))
    assert error.value.status_code == 502 and "codigo-privado" not in error.value.detail


def test_sem_codigo_nao_chama_provedor(configured, monkeypatch):
    def fail(request):
        pytest.fail("Nao deve chamar provedor sem codigo.")
    transport(monkeypatch, fail)
    with pytest.raises(HTTPException) as error:
        asyncio.run(auth_service.exchange_code_for_claims("", "verificador"))
    assert error.value.status_code == 400


def test_cancelamento_no_callback_nao_chama_provedor(configured, monkeypatch):
    def fail(request):
        pytest.fail("Nao deve trocar codigo depois de cancelamento.")
    transport(monkeypatch, fail)
    client = TestClient(create_app(), base_url="https://localhost:8443")
    client.get("/api/v1/auth/govbr/start")
    response = client.get("/api/v1/auth/govbr/callback", params={
        "state": client.cookies["thor_auth_state"], "error": "access_denied",
        "error_description": "texto-externo-nao-confiavel"})
    assert response.status_code == 400
    assert "texto-externo" not in response.text
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.parametrize("jwks", [None, [], {}, {"keys": None}, {"keys": "invalid"}])
def test_jwks_invalido_nao_produz_erro_interno(jwks):
    with pytest.raises(HTTPException) as error:
        auth_service.validate_jwt("token-invalido", jwks)
    assert error.value.status_code == 401
