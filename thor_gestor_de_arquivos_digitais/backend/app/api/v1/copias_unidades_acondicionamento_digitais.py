from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.schemas.copia_unidade_acondicionamento_digital import (
    CopiaUnidadeAcondicionamentoDigitalCreate,
    CopiaUnidadeAcondicionamentoDigitalOut,
)
from app.services.copia_unidade_acondicionamento_digital_service import (
    CopiaUnidadeAcondicionamentoDigitalService,
)

router = APIRouter()


@router.post(
    "/unidades-acondicionamento/{id_unidade_acondicionamento}/copias",
    response_model=CopiaUnidadeAcondicionamentoDigitalOut,
    status_code=status.HTTP_201_CREATED,
)
def criar_copia_unidade_acondicionamento_digital(
    id_unidade_acondicionamento: int,
    dados: CopiaUnidadeAcondicionamentoDigitalCreate,
    db: Session = Depends(db_dep),
):
    try:
        return CopiaUnidadeAcondicionamentoDigitalService.criar(
            db, id_unidade_acondicionamento, dados
        )
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/unidades-acondicionamento/{id_unidade_acondicionamento}/copias",
    response_model=list[CopiaUnidadeAcondicionamentoDigitalOut],
)
def listar_copias_unidade_acondicionamento_digital(
    id_unidade_acondicionamento: int,
    db: Session = Depends(db_dep),
    limit: int = 50,
    offset: int = 0,
):
    return CopiaUnidadeAcondicionamentoDigitalService.listar_por_unidade(
        db, id_unidade_acondicionamento, limit, offset
    )
