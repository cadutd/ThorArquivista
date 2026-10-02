from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.instrumento import Instrumento, InstrumentoCampo
from app.schemas.instrumento import InstrumentoCreate, InstrumentoUpdate
from app.schemas.instrumento_campo import InstrumentoCampoCreate, InstrumentoCampoUpdate


def listar_instrumentos(db: Session, limit: int, offset: int, q: str | None = None) -> tuple[list[Instrumento], int]:
    safe_limit = min(max(limit, 1), 100)
    safe_offset = max(offset, 0)
    query = select(Instrumento)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Instrumento.nome.ilike(pattern), Instrumento.descricao.ilike(pattern)))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Instrumento.criado_em.desc(), Instrumento.id.desc()).limit(safe_limit).offset(safe_offset)).all()
    return list(items), total


def obter_instrumento(db: Session, instrumento_id: uuid.UUID) -> Instrumento | None:
    return db.scalar(select(Instrumento).options(selectinload(Instrumento.campos)).where(Instrumento.id == instrumento_id))


def criar_instrumento(db: Session, payload: InstrumentoCreate, usuario_id: uuid.UUID | None) -> Instrumento:
    instrumento = Instrumento(**payload.model_dump(mode="json"), criado_por=usuario_id)
    db.add(instrumento)
    db.commit()
    db.refresh(instrumento)
    return instrumento


def atualizar_instrumento(db: Session, instrumento_id: uuid.UUID, payload: InstrumentoUpdate) -> Instrumento:
    instrumento = db.get(Instrumento, instrumento_id)
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    for field, value in payload.model_dump(exclude_unset=True, mode="json").items():
        setattr(instrumento, field, value)
    db.commit()
    db.refresh(instrumento)
    return instrumento


def excluir_instrumento(db: Session, instrumento_id: uuid.UUID) -> None:
    instrumento = db.get(Instrumento, instrumento_id)
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    db.delete(instrumento)
    db.commit()


def listar_campos(db: Session, instrumento_id: uuid.UUID) -> list[InstrumentoCampo]:
    _require_instrumento(db, instrumento_id)
    return list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == instrumento_id).order_by(InstrumentoCampo.ordem.asc())))


def criar_campo(db: Session, instrumento_id: uuid.UUID, payload: InstrumentoCampoCreate) -> InstrumentoCampo:
    _require_instrumento(db, instrumento_id)
    campo = InstrumentoCampo(instrumento_id=instrumento_id, **payload.model_dump(mode="json"))
    db.add(campo)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Chave de campo ja existe no instrumento.") from exc
    db.refresh(campo)
    return campo


def atualizar_campo(db: Session, instrumento_id: uuid.UUID, campo_id: uuid.UUID, payload: InstrumentoCampoUpdate) -> InstrumentoCampo:
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
    return campo


def excluir_campo(db: Session, instrumento_id: uuid.UUID, campo_id: uuid.UUID) -> None:
    campo = db.scalar(select(InstrumentoCampo).where(InstrumentoCampo.id == campo_id, InstrumentoCampo.instrumento_id == instrumento_id))
    if not campo:
        raise HTTPException(status_code=404, detail="Campo nao encontrado.")
    db.delete(campo)
    db.commit()


def _require_instrumento(db: Session, instrumento_id: uuid.UUID) -> Instrumento:
    instrumento = db.get(Instrumento, instrumento_id)
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    return instrumento
