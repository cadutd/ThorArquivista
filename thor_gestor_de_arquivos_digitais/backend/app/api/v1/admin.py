from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.admin import ConfiguracaoEnderecamento
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
