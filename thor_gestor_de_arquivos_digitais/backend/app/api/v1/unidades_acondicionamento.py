from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.unidade_acondicionamento import (
    UnidadeAcondicionamentoCreate,
    UnidadeAcondicionamentoOut,
)
from app.services.unidade_acondicionamento_service import (
    UnidadeAcondicionamentoService,
)

router = APIRouter()


@router.post(
    "",
    response_model=UnidadeAcondicionamentoOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_unidade_acondicionamento(
    dados: UnidadeAcondicionamentoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return UnidadeAcondicionamentoService.criar(db, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("", response_model=list[UnidadeAcondicionamentoOut])
def listar_unidades_acondicionamento(
    db: Session = Depends(db_dep),
    limit: int = 50,
    offset: int = 0,
):
    return UnidadeAcondicionamentoService.listar(db, limit, offset)


@router.get("/{id}", response_model=UnidadeAcondicionamentoOut)
def obter_unidade_acondicionamento(
    id: int,
    db: Session = Depends(db_dep),
):
    ua = UnidadeAcondicionamentoService.obter_por_id(db, id)
    if not ua:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade de acondicionamento não encontrada.",
        )
    return ua
