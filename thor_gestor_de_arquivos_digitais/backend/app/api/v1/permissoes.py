from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.permissao import (
    AcaoPermissao,
    PerfilCreate,
    PerfilList,
    PerfilRead,
    PerfilUpdate,
    PermissaoList,
    PermissaoRead,
)
from app.services.permissao_service import PerfilService, PermissaoService

router = APIRouter()


@router.get("/permissoes", response_model=PermissaoList)
def listar_permissoes(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    codigo: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    modulo: str | None = Query(default=None),
    funcao: str | None = Query(default=None),
    acao: AcaoPermissao | None = Query(default=None),
    ativo: bool | None = Query(default=None),
):
    items, total = PermissaoService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        codigo=codigo,
        nome=nome,
        modulo=modulo,
        funcao=funcao,
        acao=acao,
        ativo=ativo,
    )
    return PermissaoList(items=items, total=total, limit=limit, offset=offset)


@router.get("/permissoes/{id}", response_model=PermissaoRead)
def obter_permissao(id: uuid.UUID, db: Session = Depends(db_dep)):
    permissao = PermissaoService.obter_por_id(db, id)
    if not permissao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permissão não encontrada.")
    return permissao


@router.post("/perfis", response_model=PerfilRead, status_code=status.HTTP_201_CREATED)
def criar_perfil(dados: PerfilCreate, db: Session = Depends(db_dep)):
    try:
        return PerfilService.criar(db, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/perfis", response_model=PerfilList)
def listar_perfis(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    codigo: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    ativo: bool | None = Query(default=None),
    sistema: bool | None = Query(default=None),
):
    items, total = PerfilService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        codigo=codigo,
        nome=nome,
        ativo=ativo,
        sistema=sistema,
    )
    return PerfilList(items=items, total=total, limit=limit, offset=offset)


@router.get("/perfis/{id}", response_model=PerfilRead)
def obter_perfil(id: uuid.UUID, db: Session = Depends(db_dep)):
    perfil = PerfilService.obter_por_id(db, id)
    if not perfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    return perfil


@router.put("/perfis/{id}", response_model=PerfilRead)
def atualizar_perfil(id: uuid.UUID, dados: PerfilUpdate, db: Session = Depends(db_dep)):
    try:
        perfil = PerfilService.atualizar(db, id, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not perfil:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    return perfil


@router.delete("/perfis/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_perfil(id: uuid.UUID, db: Session = Depends(db_dep)):
    try:
        excluido = PerfilService.excluir(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not excluido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
