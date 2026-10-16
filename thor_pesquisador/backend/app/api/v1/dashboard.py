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
from app.services.indexacao_service import contar_jobs_falhos, jobs_recentes
from app.services.permissao_service import filtro_escopo, require_any_scope
from app.models.editorial import EditorialRegistro, EventoEditorial
from app.services.relatorio_service import jobs_dashboard

router = APIRouter()


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(db_dep),
    _usuario: Usuario = Depends(current_user),
) -> DashboardStats:
    require_any_scope(db, "dashboard_consultar")
    scope = filtro_escopo(db, Instrumento.id)
    total_instrumentos = db.scalar(select(func.count()).select_from(Instrumento).where(scope)) or 0
    total_campos = db.scalar(select(func.count()).select_from(InstrumentoCampo).where(filtro_escopo(db, InstrumentoCampo.instrumento_id))) or 0
    publicados = db.scalar(
        select(func.count()).select_from(Instrumento).where(scope, Instrumento.publicacao_id.is_not(None), Instrumento.status != "ARQUIVADO")
    ) or 0
    rascunho = db.scalar(
        select(func.count()).select_from(Instrumento).where(scope, Instrumento.status == StatusInstrumento.RASCUNHO.value)
    ) or 0
    por_tipo_rows = db.execute(
        select(Instrumento.tipo, func.count()).where(scope).group_by(Instrumento.tipo).order_by(Instrumento.tipo.asc())
    ).all()
    jobs = jobs_recentes(db)
    statuses = dict(db.execute(select(EditorialRegistro.status_operacional, func.count()).where(
        filtro_escopo(db, EditorialRegistro.instrumento_id)).group_by(EditorialRegistro.status_operacional)).all())
    pending_records = db.scalar(select(func.count()).select_from(EditorialRegistro).where(
        filtro_escopo(db, EditorialRegistro.instrumento_id), EditorialRegistro.status_editorial == "EM_REVISAO")) or 0
    pending_schemas = db.scalar(select(func.count()).select_from(Instrumento).where(scope, Instrumento.status == "EM_REVISAO")) or 0
    publications = db.scalars(select(EventoEditorial).where(EventoEditorial.acao == "publicar",
        filtro_escopo(db, EventoEditorial.instrumento_id)).order_by(EventoEditorial.criado_em.desc(), EventoEditorial.id).limit(5))

    return DashboardStats(
        jobs_conformidade=jobs_dashboard(db),
        total_instrumentos=total_instrumentos,
        pendencias_editoriais=pending_records + pending_schemas,
        publicacoes_recentes=[{"instrumento_id": str(e.instrumento_id), "registro_id": e.registro_id,
            "agente": e.agente, "data": e.criado_em.isoformat(), "versao": e.versao} for e in publications],
        instrumentos_publicados=publicados,
        instrumentos_rascunho=rascunho,
        total_campos=total_campos,
        total_registros=statuses.get("ATIVO", 0) + statuses.get("INATIVO", 0),
        registros_ativos=statuses.get("ATIVO", 0),
        registros_inativos=statuses.get("INATIVO", 0),
        instrumentos_por_tipo=[{"tipo": tipo, "total": total} for tipo, total in por_tipo_rows],
        indexacao_jobs_recentes=[
            {
                "id": str(job.id),
                "instrumento_id": str(job.instrumento_id),
                "tipo": job.tipo,
                "status": job.status,
                "processados": job.processados,
                "total_estimado": job.total_estimado,
                "erro": job.erro,
            }
            for job in jobs
        ],
        indexacao_jobs_falhos=contar_jobs_falhos(db),
    )
