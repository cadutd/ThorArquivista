from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.migracao_midia import (
    MigracaoMidiaConclusao,
    MigracaoMidiaEtapaCreate,
    MigracaoMidiaOut,
    MigracaoMidiaPage,
    MigracaoMidiaRelatorioCreate,
    MigracaoMidiaUpdate,
)
from app.security.deps import get_current_user_claims
from app.services.migracao_midia_service import MigracaoMidiaService

router = APIRouter()


@router.get("", response_model=MigracaoMidiaPage)
def listar_migracoes_midias(
    db: Session = Depends(db_dep),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    items, total = MigracaoMidiaService.listar(db, limit=limit, offset=offset)
    return MigracaoMidiaPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{migracao_id}", response_model=MigracaoMidiaOut)
def obter_migracao_midia(
    migracao_id: uuid.UUID,
    db: Session = Depends(db_dep),
):
    migracao = MigracaoMidiaService.obter(db, migracao_id)
    if not migracao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migracao de midia nao encontrada.",
        )
    return migracao


@router.put("/{migracao_id}", response_model=MigracaoMidiaOut)
def atualizar_migracao_midia(
    migracao_id: uuid.UUID,
    dados: MigracaoMidiaUpdate,
    db: Session = Depends(db_dep),
):
    migracao = MigracaoMidiaService.atualizar(db, migracao_id, dados)
    if not migracao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Migracao de midia nao encontrada.",
        )
    return migracao


@router.post("/{migracao_id}/etapas", response_model=MigracaoMidiaOut)
def registrar_etapa_migracao_midia(
    migracao_id: uuid.UUID,
    dados: MigracaoMidiaEtapaCreate,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        return MigracaoMidiaService.registrar_etapa(
            db,
            migracao_id,
            dados,
            usuario_id=_nome_usuario_claims(claims),
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{migracao_id}/relatorios", response_model=MigracaoMidiaOut)
def anexar_relatorio_migracao_midia(
    migracao_id: uuid.UUID,
    dados: MigracaoMidiaRelatorioCreate,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        return MigracaoMidiaService.anexar_relatorio(
            db,
            migracao_id,
            dados,
            usuario_id=_nome_usuario_claims(claims),
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{migracao_id}/concluir", response_model=MigracaoMidiaOut)
def concluir_migracao_midia(
    migracao_id: uuid.UUID,
    dados: MigracaoMidiaConclusao,
    db: Session = Depends(db_dep),
    claims: dict = Depends(get_current_user_claims),
):
    try:
        return MigracaoMidiaService.concluir_migracao(
            db,
            migracao_id,
            dados,
            usuario_id=_nome_usuario_claims(claims),
        )
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


def _nome_usuario_claims(claims: dict) -> str | None:
    for campo in ("name", "preferred_username", "email", "sub"):
        valor = claims.get(campo)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return None
