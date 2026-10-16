import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.editorial import AcessoInstrumento, Papel
from app.models.instrumento import Instrumento
from app.models.user import Usuario
from app.services.permissao_service import bloquear_administracao, require, permissoes, validar_concessao, ha_administrador, preservar_administrador
from app.services.usuario_service import validar_ativo


def conceder_lote(db, payload, acesso_id=None):
    db.info["operacao_id"] = uuid.uuid4()
    bloquear_administracao(db)
    actor = require(db, "acessos_editar" if acesso_id else "acessos_incluir")
    admin_antes = ha_administrador(db) if acesso_id else False
    original = db.get(AcessoInstrumento, acesso_id) if acesso_id else None
    if acesso_id and not original:
        raise HTTPException(404, "Acesso nao encontrado.")
    if original:
        validar_concessao(db, original.papel, original.instrumento_id)
        if original.usuario_id == actor.id and original.papel == "ADMIN" and (
                payload.usuario_id != actor.id or "ADMIN" not in payload.perfis or payload.escopo != "GLOBAL"):
            raise HTTPException(409, "Nao e permitido remover o proprio acesso administrativo.")
    if acesso_id and len(payload.perfis) * max(1, len(payload.instrumento_ids)) > 1:
        require(db, "acessos_incluir")
    if not db.get(Usuario, payload.usuario_id):
        raise HTTPException(404, "Usuario nao encontrado.")
    validar_ativo(db, payload.usuario_id)
    profiles = list(db.scalars(select(Papel).where(Papel.nome.in_(payload.perfis))))
    if len(profiles) != len(payload.perfis) or any(not p.ativo for p in profiles):
        raise HTTPException(422, "Selecione apenas perfis existentes e ativos.")
    instruments = list(db.scalars(select(Instrumento).where(Instrumento.id.in_(payload.instrumento_ids))))
    if len(instruments) != len(payload.instrumento_ids):
        raise HTTPException(404, "Um ou mais instrumentos nao foram encontrados.")
    scopes = payload.instrumento_ids if payload.escopo == "INSTRUMENTO" else [None]
    if payload.escopo == "INSTRUMENTO" and any(p.nome == "ADMIN" or "*" in p.permissoes for p in profiles):
        raise HTTPException(422, "Perfil administrativo irrestrito deve ter escopo global.")
    # Resolve the actor's effective permissions once per scope, not per combination.
    required = {permission for profile in profiles for permission in profile.permissoes}
    for scope in scopes:
        own = permissoes(db, scope)
        if "*" not in own and not required.issubset(own):
            raise HTTPException(403, "Nao e permitido administrar permissoes superiores as suas.")
    existing = list(db.scalars(select(AcessoInstrumento).where(
        AcessoInstrumento.usuario_id == payload.usuario_id, AcessoInstrumento.papel.in_(payload.perfis))))
    for grant in existing:
        if original and grant.id == original.id:
            continue
        if grant.instrumento_id is None or payload.escopo == "GLOBAL" or grant.instrumento_id in scopes:
            profile = next(p for p in profiles if p.nome == grant.papel)
            raise HTTPException(409, "Concessao duplicada ou sobreposta para o perfil " +
                                (profile.titulo or profile.nome) + ". Revise os acessos existentes.")
    combinations = [(profile.nome, scope) for profile in profiles for scope in scopes]
    rows = []
    if original:
        retained = (original.papel, original.instrumento_id)
        role, scope = combinations.pop(combinations.index(retained) if retained in combinations else 0)
        original.usuario_id, original.papel, original.instrumento_id = payload.usuario_id, role, scope
        rows.append(original)
    rows.extend(AcessoInstrumento(usuario_id=payload.usuario_id, papel=role, instrumento_id=scope)
                for role, scope in combinations)
    # Validation completes before any write; the edited ID and unrelated grants survive.
    db.add_all(rows)
    try:
        preservar_administrador(db, admin_antes)
        result = {"items": [{"id": str(row.id), "papel": row.papel,
                             "instrumento_id": str(row.instrumento_id) if row.instrumento_id else None}
                            for row in rows], "total": len(rows)}
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Concessao alterada simultaneamente. Revise os acessos existentes.")
    except HTTPException:
        db.rollback()
        raise
    return result
