from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.midia_armazenamento import (
    MidiaArmazenamentoCreate,
    MidiaArmazenamentoOut,
)
from app.services.midia_armazenamento_service import (
    MidiaArmazenamentoService,
)

router = APIRouter()


@router.post(
    "",
    response_model=MidiaArmazenamentoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_midia_armazenamento(
    dados: MidiaArmazenamentoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return MidiaArmazenamentoService.criar(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=list[MidiaArmazenamentoOut])
def listar_midias_armazenamento(
    db: Session = Depends(db_dep),
    limit: int = 50,
    offset: int = 0,
):
    return MidiaArmazenamentoService.listar(db, limit, offset)
