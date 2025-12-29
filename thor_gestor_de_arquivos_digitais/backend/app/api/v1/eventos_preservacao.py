from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.evento_preservacao import (
    EventoPreservacaoCreate,
    EventoPreservacaoOut,
)
from app.services.evento_preservacao_service import EventoPreservacaoService

router = APIRouter()


@router.post(
    "/unidades-acondicionamento/{id_unidade_acondicionamento}/eventos-preservacao",
    response_model=EventoPreservacaoOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_evento_preservacao(
    id_unidade_acondicionamento: int,
    dados: EventoPreservacaoCreate,
    db: Session = Depends(db_dep),
):
    try:
        return EventoPreservacaoService.registrar(
            db,
            id_unidade_acondicionamento,
            dados,
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/unidades-acondicionamento/{id_unidade_acondicionamento}/eventos-preservacao",
    response_model=list[EventoPreservacaoOut],
)
def listar_eventos_preservacao(
    id_unidade_acondicionamento: int,
    db: Session = Depends(db_dep),
    limit: int = 50,
    offset: int = 0,
):
    return EventoPreservacaoService.listar_por_unidade(
        db,
        id_unidade_acondicionamento,
        limit,
        offset,
    )


@router.get(
    "/unidades-acondicionamento/{id_unidade_acondicionamento}/eventos-preservacao/{id_evento}",
    response_model=EventoPreservacaoOut,
)
def obter_evento_preservacao(
    id_unidade_acondicionamento: int,
    id_evento: int,
    db: Session = Depends(db_dep),
):
    evento = EventoPreservacaoService.obter_por_id(
        db,
        id_unidade_acondicionamento,
        id_evento,
    )
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento de preservação não encontrado.",
        )
    return evento
