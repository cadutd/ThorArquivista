import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.api.v1.auth import safe_return_path
from app.core.config import settings
from app.tests.functional.test_editorial import ctx
from app.tests.functional.test_usuarios import criar, payload


@pytest.mark.parametrize("path", ["https://outside.example/","//outside.example/","/%2Foutside.example","/\\\\outside.example",
    "/login","/login?next=/usuarios","/a/../login","/usuarios%0d%0aLocation:x"])
def test_destino_login_rejeita_externo_e_loop(path):
    assert safe_return_path(path) == "/dashboard"


@pytest.mark.parametrize("path", ["/usuarios","/acessos/novo?usuario=abc","/instrumentos?q=Ana%20Maria","/consulta/a#imagens"])
def test_destino_login_preserva_caminho_interno(path):
    assert safe_return_path(path) == path


def test_callback_retorna_destino_validado_e_limpa_cookie(ctx,monkeypatch):
    admin, _, _ = ctx
    user = criar(admin,payload())
    from app.api.v1 import auth
    async def exchange(*args):
        return {"sub":user["cpf"],"nonce":client.cookies["thor_auth_nonce"]}
    monkeypatch.setattr(auth,"exchange_code_for_claims",exchange)
    client = TestClient(create_app())
    start = client.get("/api/v1/auth/govbr/start",params={"next":"/acessos/novo?usuario=" + user["id"]})
    assert start.status_code == 200
    state = client.cookies["thor_auth_state"]
    response = client.get("/api/v1/auth/govbr/callback",params={"code":"teste","state":state},follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == settings.public_app_url.rstrip("/") + "/acessos/novo?usuario=" + user["id"]
    assert "thor_auth_return_to" not in client.cookies
    assert client.get("/api/v1/auth/me").json()["id"] == user["id"]
