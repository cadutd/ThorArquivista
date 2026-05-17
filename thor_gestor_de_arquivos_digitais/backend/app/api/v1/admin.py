from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.admin import ConfiguracaoEnderecamento, ConfiguracaoInstituicao
from app.schemas.instituicao_arquivo import (
    InstituicaoArquivoCreate,
    InstituicaoArquivoRead,
    InstituicaoArquivoUpdate,
)
from app.services.admin_service import AdminService
from app.services.instituicao_arquivo_service import InstituicaoArquivoService

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


@router.get("/instituicao-arquivo", response_model=InstituicaoArquivoRead | None)
def obter_instituicao_arquivo(db: Session = Depends(db_dep)):
    return InstituicaoArquivoService.obter(db)


@router.post(
    "/instituicao-arquivo",
    response_model=InstituicaoArquivoRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_instituicao_arquivo(
    dados: InstituicaoArquivoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return InstituicaoArquivoService.criar(db, dados)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.put("/instituicao-arquivo", response_model=InstituicaoArquivoRead)
def atualizar_instituicao_arquivo(
    dados: InstituicaoArquivoUpdate,
    db: Session = Depends(db_dep),
):
    instituicao = InstituicaoArquivoService.atualizar(db, dados)
    if not instituicao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instituição de Arquivo não cadastrada.",
        )
    return instituicao


@router.delete("/instituicao-arquivo", status_code=status.HTTP_204_NO_CONTENT)
def excluir_instituicao_arquivo(db: Session = Depends(db_dep)):
    try:
        excluida = InstituicaoArquivoService.excluir(db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if not excluida:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instituição de Arquivo não cadastrada.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
