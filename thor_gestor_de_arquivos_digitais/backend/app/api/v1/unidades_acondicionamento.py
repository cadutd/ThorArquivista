from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.models.enums import NivelAcesso, StatusUnidade, TipoSuporte, TipoUnidade
from app.schemas.unidade_acondicionamento import (
    UnidadeAcondicionamentoCreate,
    UnidadeAcondicionamentoOut,
    UnidadeAcondicionamentoPage,
    UnidadeAcondicionamentoUpdate,
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


@router.get("", response_model=UnidadeAcondicionamentoPage)
def listar_unidades_acondicionamento(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = None,
    identificador: str | None = None,
    titulo: str | None = None,
    descricao: str | None = None,
    tipo_suporte: TipoSuporte | None = None,
    tipo_unidade: TipoUnidade | None = None,
    nivel_acesso: NivelAcesso | None = None,
    status_unidade: StatusUnidade | None = Query(default=None, alias="status"),
    criado_em_de: datetime | None = None,
    criado_em_ate: datetime | None = None,
    atualizado_em_de: datetime | None = None,
    atualizado_em_ate: datetime | None = None,
):
    items, total = UnidadeAcondicionamentoService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        identificador=identificador,
        titulo=titulo,
        descricao=descricao,
        tipo_suporte=tipo_suporte,
        tipo_unidade=tipo_unidade,
        nivel_acesso=nivel_acesso,
        status=status_unidade,
        criado_em_de=criado_em_de,
        criado_em_ate=criado_em_ate,
        atualizado_em_de=atualizado_em_de,
        atualizado_em_ate=atualizado_em_ate,
    )
    return UnidadeAcondicionamentoPage(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


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


@router.patch("/{id}", response_model=UnidadeAcondicionamentoOut)
def atualizar_unidade_acondicionamento(
    id: int,
    dados: UnidadeAcondicionamentoUpdate,
    db: Session = Depends(db_dep),
):
    try:
        ua = UnidadeAcondicionamentoService.atualizar(db, id, dados)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if not ua:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade de acondicionamento não encontrada.",
        )

    return ua


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_unidade_acondicionamento(
    id: int,
    db: Session = Depends(db_dep),
):
    try:
        excluida = UnidadeAcondicionamentoService.excluir(db, id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    if not excluida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unidade de acondicionamento não encontrada.",
        )
