from datetime import UTC, datetime
import uuid

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session
from app.core.config import Settings, settings
from app.db.session import engine
from app.models import AcessoInstrumento, AuditoriaGeral, Papel, Sessao, Usuario
from app.scripts.configurar_sistema import criar_administrador
from app.tests.functional.test_usuarios import cpf_teste


@pytest.fixture
def bootstrap():
    assert settings.database_url.rsplit("/", 1)[-1].endswith("_test")
    # Every commit/rollback stays inside this fixture's outer transaction.
    with engine.connect() as connection:
        outer = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as db:
            db.execute(select(func.pg_advisory_xact_lock(866734120)))
            db.execute(delete(AcessoInstrumento).where(AcessoInstrumento.instrumento_id.is_(None)))
            profile = db.get(Papel, "ADMIN")
            assert profile
            profile.ativo = True
            profile.permissoes = ["*"]
            db.commit()
            config = Settings(_env_file=None, **{**settings.model_dump(), "app_env": "dev"})
            data = dict(nome="Administrador Teste", username="bootstrap_" + uuid.uuid4().hex,
                        cpf=cpf_teste(), email=uuid.uuid4().hex + "@example.org")
            yield db, config, data
        outer.rollback()


def executar(ctx, **kw):
    db, config, data = ctx
    return criar_administrador(db, config, config.app_env, data, "Operador de teste / CHG-123", confirmar=True, **kw)


@pytest.mark.parametrize("environment", ["dev", "homolog", "prod"])
def test_primeiro_admin_transacional_auditado_sem_vinculo_ou_sessao(bootstrap, environment):
    db, config, data = bootstrap
    authority = "https://sso.acesso.gov.br" if environment == "prod" else "https://sso.staging.acesso.gov.br"
    config = Settings(_env_file=None, **{**config.model_dump(), "app_env": environment,
        "govbr_dev_login": environment == "dev", "dev_admin_enabled": environment == "dev",
        "session_cookie_secure": True, "app_session_secret": "s" * 48,
        "govbr_client_id": "client-sintetico", "govbr_client_secret": "secret-sintetico",
        "public_app_url": "https://portal.instituicao.gov.br", "govbr_redirect_uri": "https://api.instituicao.gov.br/api/v1/auth/govbr/callback",
        "govbr_authorize_url": authority + "/authorize", "govbr_token_url": authority + "/token", "govbr_jwks_url": authority + "/jwk"})
    ctx = db, config, data
    first = executar(ctx)
    row = db.get(Usuario, uuid.UUID(first["usuario_id"]))
    assert row.cpf == data["cpf"] and row.govbr_sub is None
    grant = db.scalar(select(AcessoInstrumento).where(AcessoInstrumento.usuario_id == row.id))
    assert grant.papel == "ADMIN" and grant.instrumento_id is None and grant.origem == "MANUAL"
    audit = db.scalar(select(AuditoriaGeral).where(AuditoriaGeral.acao == "CONFIGURACAO_INICIAL_ADMIN", AuditoriaGeral.entidade_id == str(row.id)))
    assert audit and audit.agente == "Bootstrap: Operador de teste / CHG-123" and audit.usuario_id is None
    assert data["cpf"] not in str(audit.detalhe)
    assert db.scalar(select(func.count()).select_from(Sessao).where(Sessao.usuario_id == row.id)) == 0
    row.nome = "Nome preservado"; db.commit()
    assert executar(ctx)["status"] == "ja_configurado"
    db.refresh(row)
    assert row.nome == "Nome preservado"
    assert db.scalar(select(func.count()).select_from(AcessoInstrumento).where(AcessoInstrumento.usuario_id == row.id)) == 1
    assert db.scalar(select(func.count()).select_from(AuditoriaGeral).where(AuditoriaGeral.entidade_id == str(row.id))) == 1


def test_ja_existe_admin_nao_promove_outro_usuario(bootstrap):
    db, config, data = bootstrap
    executar(bootstrap)
    second = {**data, "cpf": cpf_teste(), "username": "segundo_" + uuid.uuid4().hex, "email": "outro@example.org"}
    with pytest.raises(ValueError, match="Ja existe administrador"):
        executar((db, config, second))
    assert db.scalar(select(Usuario.id).where(Usuario.cpf == second["cpf"])) is None


def test_usuario_existente_e_preservado_e_recebe_apenas_concessao(bootstrap):
    db, _, data = bootstrap
    user = Usuario(**data, observacoes="Preservar"); db.add(user); db.commit()
    assert not executar(bootstrap)["usuario_criado"]
    db.refresh(user)
    assert user.observacoes == "Preservar" and user.govbr_sub is None


@pytest.mark.parametrize("change", ["inativo", "excluido", "outro_username", "vinculo_invalido", "email_duplicado", "cpf_dividido"])
def test_recusa_identidades_bloqueadas_ou_conflitantes(bootstrap, change):
    db, _, data = bootstrap
    user = Usuario(**data)
    if change == "inativo": user.ativo = False
    if change == "excluido": user.excluido_em = datetime.now(UTC)
    if change == "outro_username": user.username = "outro_" + uuid.uuid4().hex
    if change == "vinculo_invalido": user.govbr_sub = cpf_teste()
    if change == "email_duplicado": user.cpf, user.username = cpf_teste(), "outro_" + uuid.uuid4().hex
    if change == "cpf_dividido":
        user.username = "outro_" + uuid.uuid4().hex
        db.add(Usuario(**{**data, "cpf": cpf_teste(), "email": "segundo@example.org"}))
    db.add(user); db.commit()
    with pytest.raises(ValueError): executar(bootstrap)
    assert db.scalar(select(AcessoInstrumento.id).where(AcessoInstrumento.usuario_id == user.id)) is None


@pytest.mark.parametrize("change", ["inativo", "permissoes", "ausente"])
def test_nao_repara_perfil_admin_alterado(bootstrap, change):
    db, _, data = bootstrap
    profile = db.get(Papel, "ADMIN")
    if change == "inativo": profile.ativo = False
    if change == "permissoes": profile.permissoes = ["usuarios_consultar"]
    if change == "ausente":
        db.execute(delete(AcessoInstrumento).where(AcessoInstrumento.papel == "ADMIN")); db.delete(profile)
    db.commit()
    with pytest.raises(ValueError, match="Perfil ADMIN"): executar(bootstrap)
    assert db.scalar(select(Usuario.id).where(Usuario.cpf == data["cpf"])) is None


def test_migration_pendente_nao_grava(bootstrap):
    db, _, data = bootstrap
    db.execute(text("UPDATE alembic_version SET version_num='head_invalido'")); db.commit()
    with pytest.raises(ValueError, match="migrations"): executar(bootstrap)
    assert db.scalar(select(Usuario.id).where(Usuario.cpf == data["cpf"])) is None


def test_falha_na_auditoria_reverte_usuario_e_concessao(bootstrap, monkeypatch):
    from app.services import auditoria_service
    db, _, data = bootstrap
    def fail(*args, **kwargs): raise RuntimeError("Falha sintetica")
    monkeypatch.setattr(auditoria_service, "registrar", fail)
    with pytest.raises(RuntimeError): executar(bootstrap)
    assert db.scalar(select(Usuario.id).where(Usuario.cpf == data["cpf"])) is None


def test_local_prepara_mesma_conta_do_dev_login_sem_sessao(bootstrap):
    db, config, _ = bootstrap
    db.execute(delete(Sessao).where(Sessao.usuario_id.in_(select(Usuario.id).where(Usuario.govbr_sub == "00000000000"))))
    # Existing local account is preserved; only missing first-admin grant is created.
    result = criar_administrador(db, config, "dev", None, "Operador local", confirmar=True, local=True)
    row = db.get(Usuario, uuid.UUID(result["usuario_id"]))
    assert row.govbr_sub == "00000000000" and row.username == "desenvolvimento"
    assert criar_administrador(db, config, "dev", None, "Operador local", confirmar=True, local=True)["status"] == "ja_configurado"


@pytest.mark.parametrize("case", ["ambiente", "confirmacao", "operador", "local_desligado", "cpf_invalido", "local_homolog"])
def test_guardas_antes_de_acessar_banco(bootstrap, case):
    _, config, data = bootstrap
    environment, confirm, operator, local = "dev", True, "Operador teste", False
    if case == "ambiente": environment = "homolog"
    if case == "confirmacao": confirm = False
    if case == "operador": operator = "\n"
    if case == "local_desligado": config.dev_admin_enabled, local, data = False, True, None
    if case == "cpf_invalido": data = {**data, "cpf": "00000000000"}
    if case == "local_homolog": environment, local, data = "homolog", True, None
    with pytest.raises(ValueError):
        criar_administrador(None, config, environment, data, operator, confirmar=confirm, local=local)
