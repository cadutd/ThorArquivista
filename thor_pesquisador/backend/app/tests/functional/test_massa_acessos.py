import uuid

import pytest
from sqlalchemy import delete, func, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.editorial import AcessoInstrumento, Papel
from app.models.user import Usuario, Sessao
from app.scripts.seed_acessos import MARKER, cpf_sintetico, fixture_id, seed_acessos
from app.services.cpf import normalizar_cpf


def test_massa_acessos_idempotente_sem_administradores_e_sem_sessoes():
    assert settings.database_url.rsplit("/", 1)[-1].endswith("_test")
    with SessionLocal() as db:
        outside = {row.id: (row.nome, row.username, row.cpf, row.ativo) for row in db.scalars(
            select(Usuario).where(Usuario.id.not_in([fixture_id(i) for i in range(1, 61)])))}
        first = seed_acessos(db)
        second = seed_acessos(db)
        assert first["total"]["usuarios"] == 60 and first["total"]["perfis"] == 24
        assert second["criados"] == {"usuarios": 0, "perfis": 0, "concessoes": 0}
        users = list(db.scalars(select(Usuario).where(Usuario.id.in_([fixture_id(i) for i in range(1, 61)]))))
        assert sum(not user.ativo for user in users) == 6
        assert all(user.govbr_sub is None and user.email.endswith("@example.org") for user in users)
        assert all(normalizar_cpf(user.cpf) == user.cpf for user in users)
        profiles = list(db.scalars(select(Papel).where(Papel.descricao == MARKER)))
        assert sum(not p.ativo for p in profiles) == 2
        assert all("*" not in p.permissoes and not any(
            permission.startswith(("usuarios_", "perfis_", "acessos_")) for permission in p.permissoes) for p in profiles)
        assert db.scalar(select(func.count()).select_from(Sessao).where(Sessao.usuario_id.in_([u.id for u in users]))) == 0
        grants = list(db.scalars(select(AcessoInstrumento).where(AcessoInstrumento.usuario_id.in_([u.id for u in users]))))
        assert grants and any(g.instrumento_id is None for g in grants)
        assert not any(g.usuario_id == fixture_id(1) for g in grants)
        assert outside == {row.id: (row.nome, row.username, row.cpf, row.ativo) for row in db.scalars(
            select(Usuario).where(Usuario.id.in_(outside)))}


def test_massa_nao_sobrescreve_edicoes_nem_restaura_concessao_revogada():
    with SessionLocal() as db:
        seed_acessos(db)
        user = db.get(Usuario, fixture_id(9))
        original = user.nome
        user.nome = "Nome alterado manualmente no CRUD"
        grant = db.scalar(select(AcessoInstrumento).where(AcessoInstrumento.usuario_id == user.id).limit(1))
        if grant:
            db.delete(grant)
        db.commit()
        before = db.scalar(select(func.count()).select_from(AcessoInstrumento).where(AcessoInstrumento.usuario_id == user.id))
        assert seed_acessos(db)["criados"] == {"usuarios": 0, "perfis": 0, "concessoes": 0}
        db.refresh(user)
        assert user.nome == "Nome alterado manualmente no CRUD"
        assert db.scalar(select(func.count()).select_from(AcessoInstrumento).where(AcessoInstrumento.usuario_id == user.id)) == before
        user.nome = original
        db.commit()


def test_massa_conflito_de_cpf_reverte_toda_operacao():
    with SessionLocal() as db:
        seed_acessos(db)
        collision = Usuario(nome="Colisao sintetica", username="colisao_" + uuid.uuid4().hex, cpf=cpf_sintetico(61))
        db.add(collision); db.commit()
        try:
            with pytest.raises(ValueError, match="ja utilizado"):
                seed_acessos(db, usuarios=61, perfis=25)
            assert db.get(Usuario, fixture_id(61)) is None
            assert db.get(Papel, "MASSA_ACESSO_025") is None
        finally:
            db.execute(delete(Usuario).where(Usuario.id == collision.id)); db.commit()


@pytest.mark.parametrize("environment", ["production", "prod", "staging"])
def test_massa_recusa_ambiente_operacional(monkeypatch, environment):
    monkeypatch.setattr(settings, "app_env", environment)
    with pytest.raises(ValueError, match="somente em dev/test"):
        seed_acessos(None)


@pytest.mark.parametrize("usuarios,perfis", [(0,24), (1001,24), (60,0), (60,101)])
def test_massa_limita_volume(monkeypatch, usuarios, perfis):
    monkeypatch.setattr(settings, "app_env", "test")
    with pytest.raises(ValueError, match="Limites"):
        seed_acessos(None, usuarios, perfis)


def test_massa_dev_exige_ativacao_explicita(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "dev")
    monkeypatch.setattr(settings, "dev_admin_enabled", False)
    with pytest.raises(ValueError, match="explicitamente"):
        seed_acessos(None)
