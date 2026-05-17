from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.user import (
    IdentityAccountCreate,
    IdentityAccountRead,
    UserCreate,
    UserList,
    UserRead,
    UserRole,
    UserUpdate,
)
from app.services.identity_provider_service import IdentityProvider, create_identity_account
from app.services.user_service import UserService

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def criar_usuario(dados: UserCreate, db: Session = Depends(db_dep)):
    try:
        return UserService.criar(db, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=UserList)
def listar_usuarios(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None),
    username: str | None = Query(default=None),
    nome: str | None = Query(default=None),
    email: str | None = Query(default=None),
    papel: UserRole | None = Query(default=None),
    ativo: bool | None = Query(default=None),
):
    items, total = UserService.listar(
        db,
        limit=limit,
        offset=offset,
        q=q,
        username=username,
        nome=nome,
        email=email,
        papel=papel,
        ativo=ativo,
    )
    return UserList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{id}", response_model=UserRead)
def obter_usuario(id: uuid.UUID, db: Session = Depends(db_dep)):
    usuario = UserService.obter_por_id(db, id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return usuario


@router.post("/{id}/identity-accounts", response_model=IdentityAccountRead, status_code=status.HTTP_201_CREATED)
async def criar_conta_identidade(
    id: uuid.UUID,
    dados: IdentityAccountCreate,
    db: Session = Depends(db_dep),
):
    usuario = UserService.obter_por_id(db, id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    result = await create_identity_account(usuario, IdentityProvider(dados.provider))
    usuario_atualizado = UserService.atualizar(
        db,
        id,
        UserUpdate(keycloak_sub=result["provider_user_id"]) if dados.provider == "KEYCLOAK" else UserUpdate(),
    )
    if not usuario_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return result


@router.put("/{id}", response_model=UserRead)
def atualizar_usuario(id: uuid.UUID, dados: UserUpdate, db: Session = Depends(db_dep)):
    try:
        usuario = UserService.atualizar(db, id, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return usuario


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuario(id: uuid.UUID, db: Session = Depends(db_dep)):
    try:
        excluido = UserService.excluir(db, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if not excluido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
