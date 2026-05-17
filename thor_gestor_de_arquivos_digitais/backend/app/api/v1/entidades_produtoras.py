from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.models.enums import TipoEntidadeProdutora
from app.schemas.entidade_produtora import (
    EntidadeProdutoraCreate,
    EntidadeProdutoraList,
    EntidadeProdutoraRead,
    EntidadeProdutoraTree,
    EntidadeProdutoraUpdate,
)
from app.services.entidade_produtora_service import EntidadeProdutoraService

router = APIRouter()


@router.post("", response_model=EntidadeProdutoraRead, status_code=status.HTTP_201_CREATED)
def criar_entidade_produtora(
    dados: EntidadeProdutoraCreate,
    db: Session = Depends(db_dep),
):
    try:
        return EntidadeProdutoraService.criar(db, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=EntidadeProdutoraList)
def listar_entidades_produtoras(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    sigla: str | None = Query(default=None),
    tipo_entidade: TipoEntidadeProdutora | None = Query(default=None),
    entidade_ativa: bool | None = Query(default=None),
    id_entidade_superior: uuid.UUID | None = Query(default=None),
):
    items, total = EntidadeProdutoraService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        nome=nome,
        sigla=sigla,
        tipo_entidade=tipo_entidade,
        entidade_ativa=entidade_ativa,
        id_entidade_superior=id_entidade_superior,
    )
    return EntidadeProdutoraList(items=items, total=total, limit=limit, offset=offset)


@router.get("/arvore", response_model=list[EntidadeProdutoraTree])
def obter_arvore_entidades_produtoras(
    db: Session = Depends(db_dep),
    q: str | None = Query(default=None),
    tipo_entidade: TipoEntidadeProdutora | None = Query(default=None),
    entidade_ativa: bool | None = Query(default=None),
    parent_id: uuid.UUID | None = Query(default=None),
):
    return EntidadeProdutoraService.listar_arvore(
        db,
        q=q,
        tipo_entidade=tipo_entidade,
        entidade_ativa=entidade_ativa,
        parent_id=parent_id,
        apenas_raizes=True,
    )


@router.get("/{id}", response_model=EntidadeProdutoraRead)
def obter_entidade_produtora(id: uuid.UUID, db: Session = Depends(db_dep)):
    entidade = EntidadeProdutoraService.obter_por_id(db, id)
    if not entidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidade produtora não encontrada.",
        )
    return entidade


@router.put("/{id}", response_model=EntidadeProdutoraRead)
def atualizar_entidade_produtora(
    id: uuid.UUID,
    dados: EntidadeProdutoraUpdate,
    db: Session = Depends(db_dep),
):
    try:
        entidade = EntidadeProdutoraService.atualizar(db, id, dados)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if not entidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidade produtora não encontrada.",
        )
    return entidade


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_entidade_produtora(id: uuid.UUID, db: Session = Depends(db_dep)):
    try:
        excluida = EntidadeProdutoraService.excluir(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if not excluida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entidade produtora não encontrada.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
