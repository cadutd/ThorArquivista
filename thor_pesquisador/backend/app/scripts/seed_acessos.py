"""Synthetic access fixtures, opt-in and restricted to local development/tests."""
from __future__ import annotations

import argparse
import json
import uuid

from sqlalchemy import func, or_, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.editorial import AcessoInstrumento, Papel
from app.models.instrumento import Instrumento
from app.models.user import Usuario
from app.schemas.usuario import UsuarioIn
from app.services.permissao_service import ROLE_PERMISSIONS, bloquear_administracao

NAMESPACE = uuid.UUID("b915e0d3-72f1-4da8-a07d-dcccf56bb6ea")
MARKER = "MASSA_ACESSOS: dados sinteticos para desenvolvimento, sem vinculo gov.br."
NOMES = ("Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela", "Henrique")
SOBRENOMES = ("Almeida", "Barbosa", "Costa", "Duarte", "Esteves", "Freitas", "Gomes", "Lima")
PERFIS = ("Consulta institucional", "Catalogacao", "Revisao documental", "Pesquisa historica",
          "Acervo fotografico", "Acervo textual", "Acervo audiovisual", "Colecoes especiais")


def fixture_id(index):
    return uuid.uuid5(NAMESPACE, "usuario:" + str(index))


def cpf_sintetico(index):
    value = str(930000000 + index)
    for length in (9, 10):
        digit = sum(int(value[i]) * (length + 1 - i) for i in range(length)) * 10 % 11
        value += str(0 if digit == 10 else digit)
    return value


def seed_acessos(db, usuarios=60, perfis=24):
    if settings.app_env not in {"dev", "test"}:
        raise ValueError("Massa de testes permitida somente em dev/test.")
    if settings.app_env == "dev" and not (settings.dev_admin_enabled and settings.govbr_dev_login):
        raise ValueError("Ative explicitamente o ambiente local de desenvolvimento antes de gerar a massa.")
    if not 1 <= usuarios <= 1000 or not 1 <= perfis <= 100:
        raise ValueError("Limites: 1 a 1000 usuarios e 1 a 100 perfis.")
    bloquear_administracao(db)
    created = {"usuarios": 0, "perfis": 0, "concessoes": 0}
    codes = ["MASSA_ACESSO_" + str(i).zfill(3) for i in range(1, perfis + 1)]
    ids = [fixture_id(i) for i in range(1, usuarios + 1)]
    # Never overwrite profiles, users or grant choices edited through the CRUD.
    try:
        for i, code in enumerate(codes, 1):
            row = db.get(Papel, code)
            if row:
                if row.descricao != MARKER:
                    raise ValueError("Codigo de perfil ja utilizado fora desta massa: " + code)
                continue
            db.add(Papel(nome=code, titulo="Teste - " + PERFIS[(i-1) % len(PERFIS)] + " " + str(i).zfill(2),
                         descricao=MARKER, ativo=i % 12 != 0,
                         permissoes=ROLE_PERMISSIONS[("CONSULTA_INTERNA", "EDITOR", "REVISOR")[(i-1) % 3]]))
            created["perfis"] += 1
        db.flush()
        active = list(db.scalars(select(Papel).where(Papel.nome.in_(codes), Papel.ativo.is_(True)).order_by(Papel.nome)))
        instruments = list(db.scalars(select(Instrumento.id).order_by(Instrumento.id).limit(2)))
        for i, user_id in enumerate(ids, 1):
            existing = db.get(Usuario, user_id)
            if existing:
                if not (existing.username or "").startswith("massa_acesso_"):
                    raise ValueError("Identificador de usuario ja utilizado fora desta massa.")
                continue
            data = UsuarioIn(
                nome="Teste - " + NOMES[(i-1) % len(NOMES)] + " " + SOBRENOMES[((i-1)//8) % len(SOBRENOMES)] + " " + str(i).zfill(3),
                username="massa_acesso_" + str(i).zfill(3), cpf=cpf_sintetico(i),
                email="massa.acesso." + str(i).zfill(3) + "@example.org",
                ativo=i % 10 != 0, observacoes=MARKER)
            collision = db.scalar(select(Usuario.id).where(or_(Usuario.username == data.username, Usuario.cpf == data.cpf)))
            if collision:
                raise ValueError("CPF ou username da massa ja utilizado. Nenhum dado sera sobrescrito.")
            user = Usuario(id=user_id, **data.model_dump())
            db.add(user)
            db.flush()
            created["usuarios"] += 1
            if i <= 8 or not user.ativo or not active:
                continue
            profiles = [active[(i-1) % len(active)]]
            if len(active) > 1:
                profiles.append(active[i % len(active)])
            scopes = instruments if i > 24 and instruments else [None]
            for profile in profiles:
                for instrument_id in scopes:
                    db.add(AcessoInstrumento(usuario_id=user.id, papel=profile.nome, instrumento_id=instrument_id))
                    created["concessoes"] += 1
        db.flush()
        total = {
            "usuarios": db.scalar(select(func.count()).select_from(Usuario).where(Usuario.id.in_(ids))),
            "perfis": db.scalar(select(func.count()).select_from(Papel).where(Papel.nome.in_(codes))),
            "concessoes": db.scalar(select(func.count()).select_from(AcessoInstrumento).where(AcessoInstrumento.usuario_id.in_(ids))),
        }
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"criados": created, "total": total}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usuarios", type=int, default=60)
    parser.add_argument("--perfis", type=int, default=24)
    args = parser.parse_args()
    try:
        with SessionLocal() as db:
            result = seed_acessos(db, args.usuarios, args.perfis)
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
