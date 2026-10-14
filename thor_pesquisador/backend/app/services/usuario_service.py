from datetime import UTC, datetime
from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from app.models.editorial import AcessoInstrumento, Papel
from app.models.user import Sessao, Usuario
from app.services.permissao_service import require, validar_concessao, validar_usuario_delegado


def obter(db, usuario_id, acao="usuarios_consultar"):
    require(db, acao)
    row = db.scalar(select(Usuario).where(Usuario.id == usuario_id, Usuario.excluido_em.is_(None)).with_for_update())
    if not row:
        raise HTTPException(404, "Usuario nao encontrado.")
    return row


def dados(db, row):
    principal = db.scalar(select(AcessoInstrumento).where(
        AcessoInstrumento.usuario_id == row.id, AcessoInstrumento.origem == "USUARIO"))
    perfil = db.get(Papel, principal.papel) if principal else None
    return {"id":str(row.id), "nome":row.nome, "username":row.username, "cpf":row.cpf,
            "email":row.email, "ativo":row.ativo, "observacoes":row.observacoes,
            "govbr_vinculado":bool(row.govbr_sub and row.govbr_sub != "00000000000"),
            "perfil_codigo":principal.papel if principal else None,
            "perfil_nome":(perfil.titulo or perfil.nome) if perfil else None,
            "criado_em":row.criado_em, "atualizado_em":row.atualizado_em}


def salvar(db, payload, usuario_id=None):
    actor = require(db, "usuarios_editar" if usuario_id else "usuarios_incluir")
    row = obter(db, usuario_id, "usuarios_editar") if usuario_id else Usuario()
    if usuario_id:
        validar_usuario_delegado(db, usuario_id)
    principal = db.scalar(select(AcessoInstrumento).where(
        AcessoInstrumento.usuario_id == row.id, AcessoInstrumento.origem == "USUARIO")) if usuario_id else None
    if usuario_id and row.id == actor.id and (
            not payload.ativo or (principal and principal.papel == "ADMIN" and payload.perfil_codigo != "ADMIN")):
        raise HTTPException(409, "Nao e permitido desativar ou remover o proprio acesso administrativo.")
    if usuario_id and row.govbr_sub and row.govbr_sub != "00000000000" and row.cpf != payload.cpf:
        raise HTTPException(409, "CPF vinculado ao gov.br nao pode ser alterado.")
    perfil = db.get(Papel, payload.perfil_codigo)
    if not perfil or (not perfil.ativo and (not principal or principal.papel != perfil.nome)):
        raise HTTPException(422, "Perfil inexistente ou inativo.")
    validar_concessao(db, payload.perfil_codigo)
    for key, value in payload.model_dump(exclude={"perfil_codigo"}).items():
        setattr(row, key, value)
    try:
        db.add(row)
        db.flush()
        if not principal or principal.papel != payload.perfil_codigo:
            if principal:
                db.delete(principal)
                db.flush()
            existing = db.scalar(select(AcessoInstrumento).where(
                AcessoInstrumento.usuario_id == row.id, AcessoInstrumento.instrumento_id.is_(None),
                AcessoInstrumento.papel == payload.perfil_codigo))
            if existing:
                existing.origem = "USUARIO"
            else:
                db.add(AcessoInstrumento(usuario_id=row.id, papel=payload.perfil_codigo, origem="USUARIO"))
        if not row.ativo:
            db.execute(delete(Sessao).where(Sessao.usuario_id == row.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "CPF ou usuario ja cadastrado.")
    return dados(db, row)


def excluir(db, usuario_id):
    row = obter(db, usuario_id, "usuarios_excluir")
    validar_usuario_delegado(db, usuario_id)
    if row.id == db.info["usuario"].id:
        raise HTTPException(409, "Nao e permitido excluir o proprio usuario.")
    row.ativo = False
    row.excluido_em = datetime.now(UTC)
    db.execute(delete(Sessao).where(Sessao.usuario_id == row.id))
    db.commit()
    return {"status":"excluido"}


def validar_ativo(db, usuario_id):
    row = db.get(Usuario, usuario_id)
    if not row or not row.ativo or row.excluido_em:
        raise HTTPException(422, "Usuario inexistente ou inativo.")
