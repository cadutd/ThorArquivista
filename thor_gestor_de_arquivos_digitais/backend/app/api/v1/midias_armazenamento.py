from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.security.deps import get_current_user_claims
from app.schemas.midia_armazenamento import (
    MidiaArmazenamentoCreate,
    MidiaArmazenamentoOut,
    MidiaArmazenamentoPage,
    MidiaArmazenamentoUpdate,
)
from app.schemas.migracao_midia import MigracaoMidiaIniciar, MigracaoMidiaOut
from app.schemas.evento_midia_armazenamento import (
    EventoMidiaArmazenamentoCreate,
    EventoMidiaArmazenamentoOut,
)
from app.services.evento_midia_armazenamento_service import (
    EventoMidiaArmazenamentoService,
)
from app.services.midia_armazenamento_service import (
    MidiaArmazenamentoService,
)
from app.services.migracao_midia_service import MigracaoMidiaService

router = APIRouter()


@router.post(
    "",
    response_model=MidiaArmazenamentoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_midia_armazenamento(
    dados: MidiaArmazenamentoCreate,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        return MidiaArmazenamentoService.criar(
            db,
            dados,
            agente=_nome_usuario_claims(claims),
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=MidiaArmazenamentoPage)
def listar_midias_armazenamento(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    tipo_midia_id: uuid.UUID | None = Query(default=None),
    ativo: bool | None = Query(default=None),
):
    items, total = MidiaArmazenamentoService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        tipo_midia_id=tipo_midia_id,
        ativo=ativo,
    )
    return MidiaArmazenamentoPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put("/{midia_id}", response_model=MidiaArmazenamentoOut)
def atualizar_midia_armazenamento(
    midia_id: int,
    dados: MidiaArmazenamentoUpdate,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        midia = MidiaArmazenamentoService.atualizar(
            db,
            midia_id,
            dados,
            agente=_nome_usuario_claims(claims),
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    if not midia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Midia de armazenamento nao encontrada.",
        )
    return midia


@router.post(
    "/{midia_id}/eventos",
    response_model=EventoMidiaArmazenamentoOut,
    status_code=status.HTTP_201_CREATED,
)
@router.post(
    "/{midia_id}/eventos-preservacao",
    response_model=EventoMidiaArmazenamentoOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_evento_preservacao_midia(
    midia_id: int,
    dados: EventoMidiaArmazenamentoCreate,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        payload = dados.model_dump()
        payload["agente"] = payload.get("agente") or _nome_usuario_claims(claims)
        return EventoMidiaArmazenamentoService.registrar(
            db,
            midia_id,
            EventoMidiaArmazenamentoCreate(**payload),
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{midia_id}/migrar",
    response_model=MigracaoMidiaOut,
    status_code=status.HTTP_201_CREATED,
)
def iniciar_migracao_midia(
    midia_id: int,
    dados: MigracaoMidiaIniciar,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        return MigracaoMidiaService.iniciar_migracao(
            db,
            midia_id,
            dados,
            usuario_id=_nome_usuario_claims(claims),
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{midia_id}/eventos", response_model=list[EventoMidiaArmazenamentoOut])
@router.get("/{midia_id}/eventos-preservacao", response_model=list[EventoMidiaArmazenamentoOut])
def listar_eventos_preservacao_midia(
    midia_id: int,
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    try:
        return EventoMidiaArmazenamentoService.listar_por_midia(
            db,
            midia_id,
            limit=limit,
            offset=offset,
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{midia_id}/eventos/{evento_id}",
    response_model=EventoMidiaArmazenamentoOut,
)
@router.get(
    "/{midia_id}/eventos-preservacao/{evento_id}",
    response_model=EventoMidiaArmazenamentoOut,
)
def obter_evento_preservacao_midia(
    midia_id: int,
    evento_id: int,
    db: Session = Depends(db_dep),
):
    evento = EventoMidiaArmazenamentoService.obter_por_id(
        db,
        midia_id,
        evento_id,
    )
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de midia de armazenamento nao encontrado.",
        )
    return evento


@router.get("/{midia_id}", response_model=MidiaArmazenamentoOut)
def obter_midia_armazenamento(
    midia_id: int,
    db: Session = Depends(db_dep),
):
    midia = MidiaArmazenamentoService.obter(db, midia_id)
    if not midia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia de armazenamento não encontrada.",
        )
    return midia


def _nome_usuario_claims(claims: dict) -> str | None:
    for campo in ("name", "preferred_username", "email", "sub"):
        valor = claims.get(campo)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return None
