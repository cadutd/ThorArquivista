import uuid
from typing import Literal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, cast, String, literal, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import current_user, db_dep
from app.models.editorial import AcessoInstrumento, Papel, EditorialRegistro, PublicacaoInstrumento
from app.models.user import Usuario
from app.models.instrumento import Instrumento
from app.schemas.editorial import AcessoIn, TransicaoIn, ConcessaoLoteIn
from app.services import acesso_service
from app.services import editorial_service
from app.services import administracao_service
from app.services.usuario_service import validar_ativo
from app.services.permissao_service import permissoes, require, filtro_escopo, validar_concessao, bloquear_administracao, ha_administrador, preservar_administrador

router = APIRouter(dependencies=[Depends(current_user)])


@router.get("/editorial/fila")
def fila(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    instruments = select(Instrumento.id.label("instrumento_id"), Instrumento.nome.label("nome"),
        cast(literal(None), String).label("registro_id"), Instrumento.versao_editorial.label("versao"),
        Instrumento.atualizado_em.label("data")).where(Instrumento.status == "EM_REVISAO",
                                                      filtro_escopo(db, Instrumento.id, "editorial_consultar"))
    records = select(EditorialRegistro.instrumento_id, Instrumento.nome, EditorialRegistro.registro_id,
        EditorialRegistro.versao, EditorialRegistro.atualizado_em).join(
        Instrumento, Instrumento.id == EditorialRegistro.instrumento_id).where(
        EditorialRegistro.status_editorial == "EM_REVISAO", filtro_escopo(db, EditorialRegistro.instrumento_id, "editorial_consultar"))
    queue = instruments.union_all(records).subquery()
    total = db.scalar(select(func.count()).select_from(queue))
    rows = db.execute(select(queue).order_by(queue.c.data, queue.c.instrumento_id, queue.c.registro_id).limit(limit).offset(offset)).mappings()
    return {"items": [dict(r) for r in rows], "total": total, "limit": limit, "offset": offset}


@router.get("/usuarios")
def usuarios(q: str = "", papel: str | None = None, ativo: bool | None = None,
             nome: str = "", username: str = "", email: str = "", cpf: str = "",
             limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
             db: Session = Depends(db_dep)):
    return administracao_service.listar_usuarios(db, q, limit, offset, papel, ativo, nome, username, email, cpf)


@router.get("/instrumentos/{instrumento_id}/versoes")
def versoes(instrumento_id: uuid.UUID, limit: int = Query(20, ge=1, le=100),
            offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    require(db, "editorial_consultar", instrumento_id)
    rows = list(db.scalars(select(PublicacaoInstrumento).where(PublicacaoInstrumento.instrumento_id == instrumento_id)
        .order_by(PublicacaoInstrumento.versao.desc()).limit(limit + 1).offset(offset)))
    return {"items": [{"id": str(r.id), "versao": r.versao, "data": r.criado_em,
                      "schema": r.schema_json} for r in rows[:limit]], "has_more": len(rows) > limit}


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}/versoes")
def registro_versoes(instrumento_id: uuid.UUID, registro_id: str, limit: int = Query(20, ge=1, le=100),
                     offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    from app.models.editorial import EventoEditorial
    from app.db.mongo import snapshots_collection
    require(db, "editorial_consultar", instrumento_id)
    events = list(db.scalars(select(EventoEditorial).where(EventoEditorial.instrumento_id == instrumento_id,
        EventoEditorial.registro_id == registro_id, EventoEditorial.acao == "publicar")
        .order_by(EventoEditorial.criado_em.desc()).limit(limit + 1).offset(offset)))
    ids = [str(e.id) for e in events[:limit]]
    snapshots = {d["_id"]: d for d in snapshots_collection().find({"_id": {"$in": ids}})}
    return {"items": [{"id": str(e.id), "versao": e.versao, "data": e.criado_em,
                      "snapshot": snapshots.get(str(e.id))} for e in events[:limit]], "has_more": len(events) > limit}


@router.get("/auth/permissoes")
def acessos_efetivos(instrumento_id: uuid.UUID | None = None, db: Session = Depends(db_dep)):
    scoped = {}
    if instrumento_id is None:
        actor = db.info["usuario"]
        for instrument_id, permissions in db.execute(select(AcessoInstrumento.instrumento_id, Papel.permissoes).join(
            Papel, Papel.nome == AcessoInstrumento.papel).where(
                AcessoInstrumento.usuario_id == actor.id, AcessoInstrumento.instrumento_id.is_not(None), Papel.ativo.is_(True))):
            scoped.setdefault(str(instrument_id), set()).update(permissions)
    return {"permissoes": sorted(permissoes(db, instrumento_id)),
            "escopos": {key: sorted(value) for key, value in scoped.items()}}


@router.get("/papeis")
def papeis(db: Session = Depends(db_dep)):
    require(db, "perfis_consultar")
    return [{"nome": p.nome, "permissoes": p.permissoes} for p in db.scalars(select(Papel).order_by(Papel.nome))]


@router.get("/acessos")
def listar_acessos(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), q: str = "",
                   papel: str | None = None, usuario_id: uuid.UUID | None = None,
                   instrumento: str = "", escopo: Literal["GLOBAL", "INSTRUMENTO"] | None = None,
                   db: Session = Depends(db_dep)):
    require(db, "acessos_consultar")
    query = select(AcessoInstrumento, Usuario.nome, Usuario.username, Papel.titulo, Instrumento.nome).join(
        Usuario, Usuario.id == AcessoInstrumento.usuario_id).join(
        Papel, Papel.nome == AcessoInstrumento.papel).outerjoin(
        Instrumento, Instrumento.id == AcessoInstrumento.instrumento_id)
    if q.strip():
        pattern = "%" + q.strip() + "%"
        query = query.where(or_(Usuario.nome.ilike(pattern), Usuario.username.ilike(pattern),
                                Papel.nome.ilike(pattern), Papel.titulo.ilike(pattern),
                                Instrumento.nome.ilike(pattern)))
    if instrumento.strip():
        query = query.where(Instrumento.nome.ilike("%" + instrumento.strip() + "%"))
    if escopo:
        query = query.where(AcessoInstrumento.instrumento_id.is_(None) if escopo == "GLOBAL"
                            else AcessoInstrumento.instrumento_id.is_not(None))
    if papel:
        query = query.where(AcessoInstrumento.papel == papel)
    if usuario_id:
        query = query.where(AcessoInstrumento.usuario_id == usuario_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(AcessoInstrumento.criado_em.desc(), AcessoInstrumento.id.desc()).limit(limit).offset(offset)).all()
    return {"items": [{"id": str(a.id), "usuario_id": str(a.usuario_id), "nome": nome,
                      "username": username, "papel": a.papel, "perfil_nome": title or a.papel,
                      "instrumento_id": str(a.instrumento_id) if a.instrumento_id else None,
                      "instrumento_nome": instrument_name if a.instrumento_id else "Todos",
                      "criado_em": a.criado_em}
                     for a, nome, username, title, instrument_name in rows],
            "total": total, "limit": limit, "offset": offset}


@router.get("/acessos/{acesso_id}")
def acesso(acesso_id: uuid.UUID, db: Session = Depends(db_dep)):
    require(db, "acessos_consultar")
    row = db.get(AcessoInstrumento, acesso_id)
    if not row:
        raise HTTPException(404, "Acesso nao encontrado.")
    user = db.get(Usuario, row.usuario_id)
    instrument = db.get(Instrumento, row.instrumento_id) if row.instrumento_id else None
    profile = db.get(Papel, row.papel)
    return {"id": str(row.id), "usuario_id": str(row.usuario_id), "nome": user.nome, "username": user.username,
            "perfil_nome": (profile.titulo or profile.nome) if profile else row.papel,
            "criado_em": row.criado_em, "papel": row.papel, "instrumento_id": str(row.instrumento_id) if row.instrumento_id else None,
            "instrumento_nome": instrument.nome if instrument else "Global"}


@router.put("/acessos/{acesso_id}")
def editar_acesso(acesso_id: uuid.UUID, payload: AcessoIn, db: Session = Depends(db_dep)):
    bloquear_administracao(db)
    admin_antes = ha_administrador(db)
    actor = require(db, "acessos_editar")
    row = db.get(AcessoInstrumento, acesso_id)
    if not row:
        raise HTTPException(404, "Acesso nao encontrado.")
    if row.usuario_id == actor.id and row.papel == "ADMIN" and (
            payload.usuario_id != actor.id or payload.papel != "ADMIN" or payload.instrumento_id is not None):
        raise HTTPException(409, "Nao e permitido remover o proprio acesso administrativo.")
    if not db.get(Usuario, payload.usuario_id) or (payload.instrumento_id and not db.get(Instrumento, payload.instrumento_id)):
        raise HTTPException(404, "Usuario ou instrumento nao encontrado.")
    if payload.papel == "ADMIN" and payload.instrumento_id:
        raise HTTPException(422, "Administrador deve ter escopo global.")
    administracao_service.validar_perfil(db, payload.papel)
    validar_ativo(db, payload.usuario_id)
    validar_concessao(db, row.papel, row.instrumento_id)
    validar_concessao(db, payload.papel, payload.instrumento_id)
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    try:
        preservar_administrador(db, admin_antes)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Acesso ja concedido.")
    return {"id": str(row.id)}


@router.put("/acessos/{acesso_id}/lote")
def editar_lote(acesso_id: uuid.UUID, payload: ConcessaoLoteIn, db: Session = Depends(db_dep)):
    return acesso_service.conceder_lote(db, payload, acesso_id)


@router.post("/acessos/lote", status_code=201)
def conceder_lote(payload: ConcessaoLoteIn, db: Session = Depends(db_dep)):
    return acesso_service.conceder_lote(db, payload)


@router.post("/acessos", status_code=201)
def conceder(payload: AcessoIn, db: Session = Depends(db_dep)):
    bloquear_administracao(db)
    admin_antes = ha_administrador(db)
    require(db, "acessos_incluir")
    if not db.get(Usuario, payload.usuario_id) or (payload.instrumento_id and not db.get(Instrumento, payload.instrumento_id)):
        raise HTTPException(404, "Usuario ou instrumento nao encontrado.")
    if payload.papel == "ADMIN" and payload.instrumento_id:
        raise HTTPException(422, "Administrador deve ter escopo global.")
    administracao_service.validar_perfil(db, payload.papel)
    validar_ativo(db, payload.usuario_id)
    validar_concessao(db, payload.papel, payload.instrumento_id)
    row = AcessoInstrumento(**payload.model_dump())
    db.add(row)
    try:
        preservar_administrador(db, admin_antes)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Acesso ja concedido.")
    return {"id": str(row.id)}


@router.delete("/acessos/{acesso_id}")
def revogar(acesso_id: uuid.UUID, db: Session = Depends(db_dep)):
    bloquear_administracao(db)
    admin_antes = ha_administrador(db)
    actor = require(db, "acessos_excluir")
    row = db.get(AcessoInstrumento, acesso_id)
    if not row:
        raise HTTPException(404, "Acesso nao encontrado.")
    if row.usuario_id == actor.id and row.papel == "ADMIN":
        raise HTTPException(409, "Nao e permitido revogar o proprio acesso administrativo.")
    validar_concessao(db, row.papel, row.instrumento_id)
    db.delete(row)
    preservar_administrador(db, admin_antes)
    db.commit()
    return {"status": "ok"}


@router.post("/instrumentos/{instrumento_id}/editorial/{acao}")
def instrumento_acao(instrumento_id: uuid.UUID, acao: str, payload: TransicaoIn, db: Session = Depends(db_dep)):
    return editorial_service.transicionar(db, instrumento_id, acao, payload)


@router.post("/instrumentos/{instrumento_id}/registros/{registro_id}/editorial/{acao}")
def registro_acao(instrumento_id: uuid.UUID, registro_id: str, acao: str, payload: TransicaoIn, db: Session = Depends(db_dep)):
    return editorial_service.transicionar(db, instrumento_id, acao, payload, registro_id)


@router.get("/instrumentos/{instrumento_id}/historico")
def instrumento_historico(instrumento_id: uuid.UUID, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    return editorial_service.historico(db, instrumento_id, limit=limit, offset=offset)


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}/historico")
def registro_historico(instrumento_id: uuid.UUID, registro_id: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(db_dep)):
    return editorial_service.historico(db, instrumento_id, registro_id, limit, offset)


def _instrumento_endpoint(acao):
    def endpoint(instrumento_id: uuid.UUID, payload: TransicaoIn, db: Session = Depends(db_dep)):
        return editorial_service.transicionar(db, instrumento_id, acao, payload)
    return endpoint


def _registro_endpoint(acao):
    def endpoint(instrumento_id: uuid.UUID, registro_id: str, payload: TransicaoIn, db: Session = Depends(db_dep)):
        return editorial_service.transicionar(db, instrumento_id, acao, payload, registro_id)
    return endpoint


for acao in editorial_service.TRANSICOES:
    router.add_api_route("/instrumentos/{instrumento_id}/" + acao, _instrumento_endpoint(acao),
                         methods=["POST"], name="instrumento_" + acao)
    router.add_api_route("/instrumentos/{instrumento_id}/registros/{registro_id}/" + acao,
                         _registro_endpoint(acao), methods=["POST"], name="registro_" + acao)
