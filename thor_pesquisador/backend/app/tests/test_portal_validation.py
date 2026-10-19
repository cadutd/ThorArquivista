import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.schemas.portal import CoresPortal


@pytest.mark.parametrize("key,value", [
    ("govbr_dev_login",True),("dev_admin_enabled",True),("auth_disabled_for_tests",True),
    ("session_cookie_secure",False),("app_session_secret","short"),
    ("govbr_client_id","change-me"),("govbr_client_secret","change-me"),
    ("public_app_url","http://portal.example"),("govbr_redirect_uri","http://api.example/callback")])
def test_producao_recusa_configuracoes_inseguras(key,value):
    data=dict(app_env="prod",govbr_dev_login=False,dev_admin_enabled=False,auth_disabled_for_tests=False,
              session_cookie_secure=True,app_session_secret="x"*32,govbr_client_id="configured-id",
              govbr_client_secret="configured-secret",public_app_url="https://portal.example",
              govbr_redirect_uri="https://api.example/callback")
    Settings(_env_file=None,**data)
    with pytest.raises(ValidationError):
        Settings(_env_file=None,**{**data,key:value})


@pytest.mark.parametrize("value",["red","#fff","url(javascript:x)","</style>","", "#GG0000"])
def test_cores_so_aceitam_hexadecimal(value):
    with pytest.raises(ValidationError):
        CoresPortal(primaria=value)


def test_limites_de_corpo_e_correlacao_de_bloqueio():
    client=TestClient(create_app())
    for length,status in [("2000000",413),("-1",413),("invalid",400)]:
        assert client.post("/api/v1/auth/dev-login",headers={"Content-Length":length}).status_code==status
    response=client.post("/api/v1/auth/logout",headers={"Origin":"https://outside.example"})
    assert response.status_code==403 and response.headers.get("x-request-id")
    chunks=(b" "*200000 for _ in range(6))
    assert client.post("/api/v1/publico/instrumentos/00000000-0000-0000-0000-000000000001/buscar",
                       content=chunks,headers={"Content-Type":"application/json"}).status_code==413
