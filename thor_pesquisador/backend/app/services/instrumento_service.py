from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.mongo import registros_collection
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.schemas.instrumento import InstrumentoCreate, InstrumentoUpdate
from app.schemas.instrumento_campo import InstrumentoCampoCreate, InstrumentoCampoUpdate
from app.services.indexacao_service import enqueue_indexacao
from app.services.permissao_service import require, filtro_escopo
from app.models.editorial import EventoEditorial, EditorialRegistro
from app.services.editorial_service import invalidar_publicacao, auditar_edicao, TRANSICOES


def listar_instrumentos(db: Session, limit: int, offset: int, q: str | None = None,
                        nome: str = "", tipo: str | None = None, status: str | None = None) -> tuple[list[Instrumento], int]:
    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    query = select(Instrumento).where(filtro_escopo(db, Instrumento.id))
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Instrumento.nome.ilike(pattern), Instrumento.descricao.ilike(pattern)))
    if nome.strip():
        query = query.where(Instrumento.nome.ilike("%" + nome.strip() + "%"))
    if tipo:
        query = query.where(Instrumento.tipo == tipo)
    if status:
        query = query.where(Instrumento.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Instrumento.criado_em.desc(), Instrumento.id.desc()).limit(safe_limit).offset(safe_offset)).all()
    return list(items), total


def obter_instrumento(db: Session, instrumento_id: uuid.UUID) -> Instrumento | None:
    require(db, "instrumentos_consultar", instrumento_id)
    return db.scalar(select(Instrumento).options(selectinload(Instrumento.campos)).where(Instrumento.id == instrumento_id))


def criar_instrumento(db: Session, payload: InstrumentoCreate, usuario_id: uuid.UUID | None) -> Instrumento:
    require(db, "instrumentos_incluir")
    if payload.status.value != "RASCUNHO":
        raise HTTPException(409, "Novos instrumentos devem iniciar como rascunho.")
    instrumento = Instrumento(**payload.model_dump(mode="json"), criado_por=usuario_id)
    db.add(instrumento)
    db.commit()
    db.refresh(instrumento)
    return instrumento


def atualizar_instrumento(db: Session, instrumento_id: uuid.UUID, payload: InstrumentoUpdate) -> Instrumento:
    require(db, "instrumentos_editar", instrumento_id)
    instrumento = db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    values = payload.model_dump(exclude_unset=True, mode="json")
    if instrumento.status == "ARQUIVADO":
        raise HTTPException(409, "Reabra o instrumento pelo fluxo editorial antes de editar.")
    expected = values.pop("versao_editorial", None)
    if expected is not None and expected != instrumento.versao_editorial:
        raise HTTPException(409, "Versao alterada. Recarregue o instrumento.")
    if (instrumento.status in {"EM_REVISAO", "APROVADO", "PUBLICADO"} or instrumento.publicacao_id) and expected is None:
        raise HTTPException(409, "Informe a versao editorial para editar este instrumento.")
    if "status" in values and values.pop("status") != instrumento.status:
        raise HTTPException(409, "Use o fluxo editorial para alterar o status.")
    anterior = instrumento.status
    instrumento.versao_editorial += 1
    instrumento.status = "RASCUNHO"
    invalidar_publicacao(db, instrumento)
    for field, value in values.items():
        setattr(instrumento, field, value)
    auditar_edicao(db, instrumento_id, None, "editar", anterior, "RASCUNHO", instrumento.versao_editorial)
    db.commit()
    db.refresh(instrumento)
    return instrumento


def excluir_instrumento(db: Session, instrumento_id: uuid.UUID, usuario_id=None) -> None:
    require(db, "instrumentos_excluir", instrumento_id)
    instrumento = db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    if instrumento.publicacao_id or db.scalar(select(EventoEditorial.id).where(
            EventoEditorial.instrumento_id == instrumento_id, EventoEditorial.acao.in_(TRANSICOES)).limit(1)):
        raise HTTPException(409, "Instrumento com historico editorial deve ser arquivado.")
    db.query(EditorialRegistro).filter(EditorialRegistro.instrumento_id == instrumento_id).delete()
    registros_collection().delete_many({"instrumento_id": str(instrumento_id)})
    from app.services.imagem_service import limpar_vinculos
    limpar_vinculos(db, instrumento_id, usuario_id=usuario_id)
    db.delete(instrumento)
    db.commit()


def listar_campos(db: Session, instrumento_id: uuid.UUID) -> list[InstrumentoCampo]:
    require(db, "campos_consultar", instrumento_id)
    _require_instrumento(db, instrumento_id)
    return list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == instrumento_id).order_by(InstrumentoCampo.ordem.asc())))


def criar_campo(db: Session, instrumento_id: uuid.UUID, payload: InstrumentoCampoCreate) -> InstrumentoCampo:
    _editar_schema(db, instrumento_id, "campos_incluir")
    campo = InstrumentoCampo(instrumento_id=instrumento_id, **payload.model_dump(mode="json"))
    db.add(campo)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave de campo ja existe no instrumento.") from exc
    db.refresh(campo)
    enqueue_indexacao({"tipo": "schema", "instrumento_id": str(instrumento_id)})
    return campo


def atualizar_campo(db: Session, instrumento_id: uuid.UUID, campo_id: uuid.UUID, payload: InstrumentoCampoUpdate) -> InstrumentoCampo:
    _editar_schema(db, instrumento_id, "campos_editar")
    campo = db.scalar(select(InstrumentoCampo).where(InstrumentoCampo.id == campo_id, InstrumentoCampo.instrumento_id == instrumento_id))
    if not campo:
        raise HTTPException(status_code=404, detail="Campo nao encontrado.")
    for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(campo, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave de campo ja existe no instrumento.") from exc
    db.refresh(campo)
    enqueue_indexacao({"tipo": "schema", "instrumento_id": str(instrumento_id)})
    return campo


def excluir_campo(db: Session, instrumento_id: uuid.UUID, campo_id: uuid.UUID) -> None:
    _editar_schema(db, instrumento_id, "campos_excluir")
    campo = db.scalar(select(InstrumentoCampo).where(InstrumentoCampo.id == campo_id, InstrumentoCampo.instrumento_id == instrumento_id))
    if not campo:
        raise HTTPException(status_code=404, detail="Campo nao encontrado.")
    db.delete(campo)
    db.commit()
    enqueue_indexacao({"tipo": "schema", "instrumento_id": str(instrumento_id)})


def _editar_schema(db, instrumento_id, acao):
    require(db, acao, instrumento_id)
    instrumento = db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    if not instrumento:
        raise HTTPException(404, "Instrumento nao encontrado.")
    anterior = instrumento.status
    instrumento.status = "RASCUNHO"
    instrumento.versao_editorial += 1
    instrumento.schema_version += 1
    invalidar_publicacao(db, instrumento)
    auditar_edicao(db, instrumento_id, None, "editar_schema", anterior, "RASCUNHO", instrumento.versao_editorial)
    return instrumento


def _require_instrumento(db: Session, instrumento_id: uuid.UUID) -> Instrumento:
    instrumento = db.get(Instrumento, instrumento_id)
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    return instrumento
