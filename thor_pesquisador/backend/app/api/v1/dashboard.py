from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_user, db_dep
from app.db.mongo import registros_collection
from app.models.enums import StatusInstrumento, StatusRegistro
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.models.user import Usuario
from app.schemas.dashboard import DashboardStats

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(db_dep),
    _usuario: Usuario = Depends(current_user),
) -> DashboardStats:
    collection = registros_collection()
    total_instrumentos = db.scalar(select(func.count()).select_from(Instrumento)) or 0
    total_campos = db.scalar(select(func.count()).select_from(InstrumentoCampo)) or 0
    publicados = db.scalar(
        select(func.count()).select_from(Instrumento).where(Instrumento.status == StatusInstrumento.PUBLICADO.value)
    ) or 0
    rascunho = db.scalar(
        select(func.count()).select_from(Instrumento).where(Instrumento.status == StatusInstrumento.RASCUNHO.value)
    ) or 0
    por_tipo_rows = db.execute(
        select(Instrumento.tipo, func.count()).group_by(Instrumento.tipo).order_by(Instrumento.tipo.asc())
    ).all()

    return DashboardStats(
        total_instrumentos=total_instrumentos,
        instrumentos_publicados=publicados,
        instrumentos_rascunho=rascunho,
        total_campos=total_campos,
        total_registros=collection.count_documents({"status": {"$ne": StatusRegistro.EXCLUIDO.value}}),
        registros_ativos=collection.count_documents({"status": StatusRegistro.ATIVO.value}),
        registros_inativos=collection.count_documents({"status": StatusRegistro.INATIVO.value}),
        instrumentos_por_tipo=[{"tipo": tipo, "total": total} for tipo, total in por_tipo_rows],
    )
