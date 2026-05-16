from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.ficha_espelho import (
    FichaEspelhoGerada,
    FichaEspelhoGerarRequest,
    ModeloFichaEspelhoCreate,
    ModeloFichaEspelhoPage,
    ModeloFichaEspelhoRead,
    ModeloFichaEspelhoUpdate,
)
from app.services.ficha_espelho_service import FichaEspelhoService

router = APIRouter()


@router.get("/modelos", response_model=ModeloFichaEspelhoPage)
def listar_modelos(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
    ativo: bool | None = None,
):
    items, total = FichaEspelhoService.listar_modelos(db, limit=limit, offset=offset, q=q, ativo=ativo)
    return ModeloFichaEspelhoPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/modelos/padrao", response_model=ModeloFichaEspelhoRead)
def obter_modelo_padrao(db: Session = Depends(db_dep)):
    return FichaEspelhoService.obter_ou_criar_modelo_padrao(db)


@router.get("/modelos/{modelo_id}", response_model=ModeloFichaEspelhoRead)
def obter_modelo(modelo_id: int, db: Session = Depends(db_dep)):
    modelo = FichaEspelhoService.obter_modelo(db, modelo_id)
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo de ficha espelho não encontrado.")
    return modelo


@router.post("/modelos", response_model=ModeloFichaEspelhoRead, status_code=status.HTTP_201_CREATED)
def criar_modelo(dados: ModeloFichaEspelhoCreate, db: Session = Depends(db_dep)):
    try:
        return FichaEspelhoService.criar_modelo(db, dados)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/modelos/{modelo_id}", response_model=ModeloFichaEspelhoRead)
def atualizar_modelo(modelo_id: int, dados: ModeloFichaEspelhoUpdate, db: Session = Depends(db_dep)):
    try:
        modelo = FichaEspelhoService.atualizar_modelo(db, modelo_id, dados)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo de ficha espelho não encontrado.")
    return modelo


@router.delete("/modelos/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_modelo(modelo_id: int, db: Session = Depends(db_dep)):
    if not FichaEspelhoService.excluir_modelo(db, modelo_id):
        raise HTTPException(status_code=404, detail="Modelo de ficha espelho não encontrado.")


@router.post("/gerar", response_model=FichaEspelhoGerada)
def gerar_fichas(dados: FichaEspelhoGerarRequest, db: Session = Depends(db_dep)):
    try:
        return FichaEspelhoService.gerar(db, dados)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
