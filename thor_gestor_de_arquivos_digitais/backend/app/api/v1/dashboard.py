from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import db_dep
from app.models.enums import StatusUnidade, TipoUnidade
from app.models.midia_armazenamento import MidiaArmazenamento
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.schemas.dashboard import DashboardStats, DashboardSupportCount

router = APIRouter()


@router.get("", response_model=DashboardStats)
def obter_dashboard(db: Session = Depends(db_dep)):
    total_unidades = db.query(func.count(UnidadeAcondicionamento.id)).scalar() or 0
    aips_digitais = (
        db.query(func.count(UnidadeAcondicionamento.id))
        .filter(UnidadeAcondicionamento.tipo_unidade == TipoUnidade.AIP)
        .scalar()
        or 0
    )
    midias_ativas = (
        db.query(func.count(MidiaArmazenamento.id))
        .filter(MidiaArmazenamento.ativo.is_(True))
        .scalar()
        or 0
    )
    alertas = (
        db.query(func.count(UnidadeAcondicionamento.id))
        .filter(UnidadeAcondicionamento.status != StatusUnidade.ATIVA)
        .scalar()
        or 0
    )
    suporte_rows = (
        db.query(
            UnidadeAcondicionamento.tipo_suporte,
            func.count(UnidadeAcondicionamento.id),
        )
        .group_by(UnidadeAcondicionamento.tipo_suporte)
        .all()
    )

    return DashboardStats(
        total_unidades=total_unidades,
        aips_digitais=aips_digitais,
        midias_ativas=midias_ativas,
        alertas=alertas,
        unidades_por_suporte=[
            DashboardSupportCount(
                tipo_suporte=tipo_suporte.value,
                total=total,
            )
            for tipo_suporte, total in suporte_rows
        ],
    )
