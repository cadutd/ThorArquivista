from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.midia_armazenamento import (
    TipoMidiaArmazenamentoCreate,
    TipoMidiaArmazenamentoOut,
    TipoMidiaArmazenamentoPage,
    TipoMidiaArmazenamentoUpdate,
)
from app.services.midia_armazenamento_service import TipoMidiaArmazenamentoService

router = APIRouter()


@router.get("", response_model=TipoMidiaArmazenamentoPage)
def listar_tipos_midia_armazenamento(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    ativo: bool | None = Query(default=None),
):
    items, total = TipoMidiaArmazenamentoService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        ativo=ativo,
    )
    return TipoMidiaArmazenamentoPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{tipo_id}", response_model=TipoMidiaArmazenamentoOut)
def obter_tipo_midia_armazenamento(
    tipo_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    tipo = TipoMidiaArmazenamentoService.obter(db, tipo_id)
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de midia de armazenamento nao encontrado.",
        )
    return tipo


@router.post(
    "",
    response_model=TipoMidiaArmazenamentoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_tipo_midia_armazenamento(
    dados: TipoMidiaArmazenamentoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return TipoMidiaArmazenamentoService.criar(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.put("/{tipo_id}", response_model=TipoMidiaArmazenamentoOut)
def atualizar_tipo_midia_armazenamento(
    tipo_id: uuid.UUID,
    dados: TipoMidiaArmazenamentoUpdate,
    db: Session = Depends(db_dep),
):
    try:
        tipo = TipoMidiaArmazenamentoService.atualizar(db, tipo_id, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de midia de armazenamento nao encontrado.",
        )
    return tipo


@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_tipo_midia_armazenamento(
    tipo_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    removido = TipoMidiaArmazenamentoService.excluir(db, tipo_id)
    if not removido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo de midia de armazenamento nao encontrado.",
        )
