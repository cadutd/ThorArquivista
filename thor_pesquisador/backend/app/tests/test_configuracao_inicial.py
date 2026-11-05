import json
import os
import subprocess
import sys

import pytest
from dotenv import dotenv_values
from app.scripts.configurar_sistema import gerar_config, modelo, preparar_config


def entrada(ambiente="homolog"):
    data = modelo(ambiente)
    for key in data:
        if "SUBSTITUIR" in data[key]:
            data[key] = "credencial-sintetica-para-testes"
    data.update(PUBLIC_APP_URL="https://portal.instituicao.gov.br",
                API_BASE_URL="https://api.instituicao.gov.br/api/v1",
                DATABASE_URL="postgresql+psycopg://test:password@postgres:5432/homolog",
                MONGODB_URL="mongodb://test:password@mongo:27017/homolog",
                REDIS_URL="redis://redis:6379/0", MEILISEARCH_URL="http://meili:7700",
                S3_ENDPOINT_URL="https://storage.instituicao.gov.br")
    return data


@pytest.mark.parametrize("environment", ["dev", "homolog", "prod"])
def test_config_por_ambiente_sem_segredos_em_configmap(tmp_path, environment):
    target = tmp_path / environment
    result = gerar_config(environment, {} if environment == "dev" else entrada(environment), target)
    config = (target / "config.env").read_text()
    private = dotenv_values(target / "secrets.env")
    assert "GOVBR_CLIENT_SECRET=" not in config and "DATABASE_URL=" not in config
    assert "APP_SESSION_SECRET=" not in config and "REDIS_URL=" not in config
    assert len(private["APP_SESSION_SECRET"]) >= 32
    assert f"APP_ENV={environment}\n" in config
    assert f"GOVBR_DEV_LOGIN={str(environment == 'dev').lower()}\n" in config
    assert f"DEV_ADMIN_ENABLED={str(environment == 'dev').lower()}\n" in config
    assert "AUTH_DISABLED_FOR_TESTS=false\n" in config
    provider = "sso.acesso.gov.br" if environment == "prod" else "sso.staging.acesso.gov.br"
    assert provider in config
    assert (target / ".env").exists() == (environment == "dev")
    assert private["APP_SESSION_SECRET"] not in json.dumps(result)
    if os.name != "nt":
        assert (target.stat().st_mode & 0o077) == 0
        assert all((p.stat().st_mode & 0o077) == 0 for p in target.iterdir())


def test_dev_preserva_dolar_aspas_e_barra_no_env_do_compose(tmp_path):
    value = "x" * 35 + "$segredo'barra\\final"
    gerar_config("dev", {"APP_SESSION_SECRET": value}, tmp_path / "dev")
    # Compose expands $$ to a literal dollar; python-dotenv intentionally does not.
    assert dotenv_values(tmp_path / "dev/.env")["APP_SESSION_SECRET"].replace("$$", "$") == value


def test_geracao_nao_sobrescreve_e_nao_rotaciona_segredo(tmp_path):
    gerar_config("dev", {}, tmp_path / "dev")
    before = (tmp_path / "dev/secrets.env").read_bytes()
    with pytest.raises(FileExistsError):
        gerar_config("dev", {}, tmp_path / "dev")
    assert (tmp_path / "dev/secrets.env").read_bytes() == before


@pytest.mark.parametrize("key,value", [
    ("PUBLIC_APP_URL", "http://portal.instituicao.gov.br"),
    ("PUBLIC_APP_URL", "https://localhost"),
    ("PUBLIC_APP_URL", "https://portal.instituicao.gov.br/subpasta"),
    ("API_BASE_URL", "https://api.instituicao.gov.br/errado"),
    ("API_BASE_URL", "https://api.instituicao.gov.br/api/v1?x=1"),
    ("DATABASE_URL", "postgresql+psycopg://postgres/homolog"),
    ("MONGODB_URL", "mongodb://mongo/homolog"),
    ("REDIS_URL", "http://redis"), ("GOVBR_CLIENT_SECRET", "change-me"),
    ("APP_SESSION_SECRET", "short"), ("S3_FORCE_PATH_STYLE", "yes"),
    ("GOVBR_CLIENT_SECRET", "privado\nAPP_ENV=dev"),
    ("APP_ENV", "dev"), ("GOVBR_DEV_LOGIN", "true"), ("PUBLIC_APP_URL", None),
])
def test_config_invalida_nao_cria_arquivos(tmp_path, key, value):
    with pytest.raises(ValueError):
        gerar_config("homolog", {**entrada(), key: value}, tmp_path / "novo")
    assert not (tmp_path / "novo").exists()


@pytest.mark.parametrize("environment", ["homolog", "prod"])
def test_template_operacional_nao_e_config_valida(environment):
    with pytest.raises(ValueError, match="Substitua"):
        preparar_config(environment, modelo(environment))


def test_modelo_funciona_sem_importar_settings_inseguros_de_producao():
    env = {k: v for k, v in os.environ.items() if k.lower() not in {"app_env", "govbr_dev_login"}}
    env.update(APP_ENV="prod", GOVBR_DEV_LOGIN="true")
    result = subprocess.run([sys.executable, "-m", "app.scripts.configurar_sistema", "modelo", "--ambiente", "prod"],
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0
    assert json.loads(result.stdout)["GOVBR_CLIENT_SECRET"] == "SUBSTITUIR"


def test_cli_json_invalido_nao_expoe_segredos():
    result = subprocess.run([sys.executable, "-m", "app.scripts.configurar_sistema", "gerar-config",
                             "--ambiente", "homolog", "--entrada", "-", "--destino", "/tmp/nao-criar"],
                            input='{"segredo-privado":', capture_output=True, text=True)
    assert result.returncode == 1
    assert "segredo-privado" not in result.stderr and "Traceback" not in result.stderr


def test_cli_ajuda_nao_acessa_banco():
    result = subprocess.run([sys.executable, "-m", "app.scripts.configurar_sistema", "--help"], capture_output=True, text=True)
    assert result.returncode == 0 and "administrador" in result.stdout


def test_cli_url_malformada_nao_expoe_credencial(tmp_path):
    data = entrada()
    data["MONGODB_URL"] = "mongodb://user:segredo-privado@host\uff0foutro"
    result = subprocess.run([sys.executable, "-m", "app.scripts.configurar_sistema", "gerar-config",
                             "--ambiente", "homolog", "--entrada", "-", "--destino", str(tmp_path / "saida")],
                            input=json.dumps(data), capture_output=True, text=True)
    assert result.returncode == 1
    assert "segredo-privado" not in result.stderr and "Traceback" not in result.stderr
    assert not (tmp_path / "saida").exists()
