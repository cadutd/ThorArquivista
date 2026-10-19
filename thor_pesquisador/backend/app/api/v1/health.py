from fastapi import APIRouter, Depends, HTTPException
from datetime import UTC, datetime
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select, text
from app.api.deps import current_user, db_dep
from app.db.mongo import get_mongo_client
from app.services.permissao_service import require
import json
from functools import lru_cache
from pathlib import Path
from alembic.script import ScriptDirectory

router = APIRouter()


@lru_cache
def expected_revision():
    return ScriptDirectory(str(Path(__file__).resolve().parents[3] / "alembic")).get_current_head()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(db=Depends(db_dep)):
    try:
        db.execute(text("SELECT 1"))
        if db.scalar(text("SELECT version_num FROM alembic_version")) != expected_revision():
            raise RuntimeError("Migration pendente.")
        get_mongo_client().admin.command("ping", maxTimeMS=2000)
    except Exception:
        raise HTTPException(503, "Dependencias essenciais indisponiveis.") from None
    return {"status": "ready"}


@router.get("/operacao/metricas", dependencies=[Depends(current_user)], response_class=PlainTextResponse)
def metricas(db=Depends(db_dep)):
    require(db, "dashboard_consultar")
    from app.models.conformidade import Exportacao, ExecucaoRetencao
    from app.models.instrumento import IndexacaoJob, Instrumento
    lines = ["# HELP thor_jobs Quantidade atual de jobs por modulo e estado.",
             "# TYPE thor_jobs gauge", "# TYPE thor_jobs_idade_max_segundos gauge",
             "# TYPE thor_jobs_sem_progresso_max_segundos gauge", "# TYPE thor_jobs_processados gauge"]
    now = datetime.now(UTC)
    for name, model in (("indexacao", IndexacaoJob), ("exportacao", Exportacao), ("retencao", ExecucaoRetencao)):
        for state, count, created, updated, processed in db.execute(select(
                model.status, func.count(), func.min(model.criado_em), func.min(model.atualizado_em),
                func.coalesce(func.sum(model.processados), 0)).group_by(model.status)):
            # State is from the closed job enum, never a user/record identifier.
            labels = '{modulo="' + name + '",estado=' + json.dumps(state) + '} '
            lines.append('thor_jobs' + labels + str(count))
            lines.append('thor_jobs_processados' + labels + str(processed))
            if state in {"PENDENTE", "PROCESSANDO"}:
                lines.append('thor_jobs_idade_max_segundos' + labels + str(max(0, (now-created).total_seconds())))
                lines.append('thor_jobs_sem_progresso_max_segundos' + labels + str(max(0, (now-updated).total_seconds())))
    retries = db.scalar(select(func.coalesce(func.sum(Exportacao.tentativa-1), 0)))
    lag = db.scalar(select(func.count()).select_from(Instrumento).where(
        Instrumento.publicacao_id.is_not(None), Instrumento.geracao_publica != Instrumento.geracao_indexada))
    lines += ["# TYPE thor_exportacao_retentativas gauge", "thor_exportacao_retentativas " + str(retries),
              "# TYPE thor_publicacoes_indexacao_pendente gauge", "thor_publicacoes_indexacao_pendente " + str(lag)]
    from app.core.observability import HTTP_BUCKETS, http_metrics, metrics_lock
    lines += ["# TYPE thor_http_requests_total counter", "# TYPE thor_http_duration_seconds histogram"]
    with metrics_lock:
        snapshot = [(key, value[0], value[1], list(value[2])) for key,value in http_metrics.items()]
    for (route, method, status), count, duration, buckets in snapshot:
        labels = 'rota='+json.dumps(route)+',metodo='+json.dumps(method)+',classe='+json.dumps(status)
        lines.append('thor_http_requests_total{'+labels+'} '+str(count))
        lines += ['thor_http_duration_seconds_bucket{'+labels+',le="'+str(bound)+'"} '+str(value)
                  for bound,value in zip(HTTP_BUCKETS,buckets)]
        lines += ['thor_http_duration_seconds_bucket{'+labels+',le="+Inf"} '+str(count),
                  'thor_http_duration_seconds_count{'+labels+'} '+str(count),
                  'thor_http_duration_seconds_sum{'+labels+'} '+str(duration)]
    return PlainTextResponse("\n".join(lines)+"\n", media_type="text/plain; version=0.0.4")
