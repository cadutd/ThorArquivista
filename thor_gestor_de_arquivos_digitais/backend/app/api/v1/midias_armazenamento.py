from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.models.enums import TipoMidiaArmazenamento
from app.schemas.midia_armazenamento import (
    MidiaArmazenamentoCreate,
    MidiaArmazenamentoOut,
    MidiaArmazenamentoPage,
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


@router.get("", response_model=MidiaArmazenamentoPage)
def listar_midias_armazenamento(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    tipo: TipoMidiaArmazenamento | None = None,
    ativo: bool | None = Query(default=None),
):
    items, total = MidiaArmazenamentoService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        tipo=tipo,
        ativo=ativo,
    )
    return MidiaArmazenamentoPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
