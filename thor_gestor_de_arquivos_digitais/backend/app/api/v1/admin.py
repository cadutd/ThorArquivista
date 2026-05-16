from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.admin import ConfiguracaoEnderecamento, ConfiguracaoInstituicao
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/configuracoes/enderecamento", response_model=ConfiguracaoEnderecamento)
def obter_configuracao_enderecamento(db: Session = Depends(db_dep)):
    return AdminService.obter_configuracao_enderecamento(db)


@router.put("/configuracoes/enderecamento", response_model=ConfiguracaoEnderecamento)
def salvar_configuracao_enderecamento(
    dados: ConfiguracaoEnderecamento,
    db: Session = Depends(db_dep),
):
    return AdminService.salvar_configuracao_enderecamento(db, dados)


@router.get("/configuracoes/instituicao", response_model=ConfiguracaoInstituicao)
def obter_configuracao_instituicao(db: Session = Depends(db_dep)):
    return AdminService.obter_configuracao_instituicao(db)


@router.put("/configuracoes/instituicao", response_model=ConfiguracaoInstituicao)
def salvar_configuracao_instituicao(
    dados: ConfiguracaoInstituicao,
    db: Session = Depends(db_dep),
):
    return AdminService.salvar_configuracao_instituicao(db, dados)
