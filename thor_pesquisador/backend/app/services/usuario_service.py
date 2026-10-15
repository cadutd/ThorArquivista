from datetime import UTC, datetime
from fastapi import HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from app.models.editorial import AcessoInstrumento, Papel
from app.models.user import Sessao, Usuario
from app.services.permissao_service import require, validar_usuario_delegado, bloquear_administracao, ha_administrador, preservar_administrador


def obter(db, usuario_id, acao="usuarios_consultar"):
    require(db, acao)
    row = db.scalar(select(Usuario).where(Usuario.id == usuario_id, Usuario.excluido_em.is_(None)).with_for_update())
    if not row:
        raise HTTPException(404, "Usuario nao encontrado.")
    return row


def resumos_acessos(db, usuario_ids):
    ids = list(usuario_ids)
    result = {user_id: {"perfis": [], "total_acessos": 0, "tem_acesso": False} for user_id in ids}
    if not ids:
        return result
    for user_id, count in db.execute(select(AcessoInstrumento.usuario_id, func.count()).where(
            AcessoInstrumento.usuario_id.in_(ids)).group_by(AcessoInstrumento.usuario_id)):
        result[user_id]["total_acessos"] = count
    profiles = db.execute(select(AcessoInstrumento.usuario_id, Papel.nome, Papel.titulo,
        Papel.ativo, Papel.permissoes, AcessoInstrumento.instrumento_id.is_(None).label("global")).join(Papel).where(
        AcessoInstrumento.usuario_id.in_(ids)).distinct().order_by(Papel.nome))
    seen = set()
    for user_id, code, title, active, permissions, global_scope in profiles:
        if (user_id, code) not in seen:
            result[user_id]["perfis"].append({"codigo": code, "nome": title or code, "ativo": active})
            seen.add((user_id, code))
        usable = permissions if global_scope else [
            p for p in permissions if not p.startswith(("usuarios_", "perfis_", "acessos_", "permissoes_"))
            and p not in {"instrumentos_incluir", "consulta_publicada", "*"}]
        result[user_id]["tem_acesso"] |= bool(active and usable)
    return result


def dados(db, row):
    access = resumos_acessos(db, [row.id])[row.id]
    return {"id":str(row.id), "nome":row.nome, "username":row.username, "cpf":row.cpf,
            "email":row.email, "ativo":row.ativo, "observacoes":row.observacoes,
            "govbr_vinculado":bool(row.govbr_sub and row.govbr_sub != "00000000000"),
            **access, "tem_acesso":bool(row.ativo and access["tem_acesso"]),
            "criado_em":row.criado_em, "atualizado_em":row.atualizado_em}


def salvar(db, payload, usuario_id=None):
    if usuario_id:
        bloquear_administracao(db)
    admin_antes = ha_administrador(db) if usuario_id else False
    actor = require(db, "usuarios_editar" if usuario_id else "usuarios_incluir")
    row = obter(db, usuario_id, "usuarios_editar") if usuario_id else Usuario()
    if usuario_id:
        validar_usuario_delegado(db, usuario_id)
    if usuario_id and row.id == actor.id and not payload.ativo:
        raise HTTPException(409, "Nao e permitido desativar o proprio usuario.")
    if usuario_id and row.govbr_sub and row.govbr_sub != "00000000000" and row.cpf != payload.cpf:
        raise HTTPException(409, "CPF vinculado ao gov.br nao pode ser alterado.")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    try:
        db.add(row)
        db.flush()
        preservar_administrador(db, admin_antes)
        if not row.ativo:
            db.execute(delete(Sessao).where(Sessao.usuario_id == row.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "CPF ou usuario ja cadastrado.")
    return dados(db, row)


def excluir(db, usuario_id):
    bloquear_administracao(db)
    admin_antes = ha_administrador(db)
    row = obter(db, usuario_id, "usuarios_excluir")
    validar_usuario_delegado(db, usuario_id)
    if row.id == db.info["usuario"].id:
        raise HTTPException(409, "Nao e permitido excluir o proprio usuario.")
    row.ativo = False
    row.excluido_em = datetime.now(UTC)
    preservar_administrador(db, admin_antes)
    db.execute(delete(Sessao).where(Sessao.usuario_id == row.id))
    db.commit()
    return {"status":"excluido"}


def validar_ativo(db, usuario_id):
    row = db.get(Usuario, usuario_id)
    if not row or not row.ativo or row.excluido_em:
        raise HTTPException(422, "Usuario inexistente ou inativo.")
