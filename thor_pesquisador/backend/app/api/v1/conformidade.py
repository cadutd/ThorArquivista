import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.api.deps import current_user, db_dep
from app.db.session import SessionLocal
from app.schemas.conformidade import ExportacaoIn, PoliticaIn, RetencaoIn, ImpedimentoIn
from app.services import auditoria_service as audit, exportacao_service as exports, retencao_service as retention
from app.services.relatorio_service import resumo, registros_por_instrumento, alteracoes_usuarios

router = APIRouter(dependencies=[Depends(current_user)])


@router.get("/conformidade/instrumentos")
def instrumentos(acao: str = "exportacoes_incluir", q: str = Query("", max_length=100),
                  limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                  db: Session = Depends(db_dep)):
    from app.models.instrumento import Instrumento
    from app.services.permissao_service import filtro_escopo, require_any_scope
    if acao not in {"exportacoes_incluir", "retencao_incluir", "retencao_editar", "auditoria_consultar", "relatorios_consultar"}:
        raise HTTPException(422, "Operacao de pesquisa invalida.")
    require_any_scope(db, acao)
    filters = [filtro_escopo(db, Instrumento.id, acao)]
    if q:
        filters.append(Instrumento.nome.ilike("%" + q + "%"))
    return {"items": [{"id": str(i.id), "nome": i.nome, "tipo": i.tipo} for i in db.scalars(
        select(Instrumento).where(*filters).order_by(Instrumento.nome, Instrumento.id).limit(limit).offset(offset))],
        "total": db.scalar(select(func.count()).select_from(Instrumento).where(*filters))}


@router.get("/auditoria")
def auditoria(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
              q: str = Query("", max_length=100), acao: str | None = None, usuario_id: uuid.UUID | None = None,
              entidade: str | None = None, instrumento_id: uuid.UUID | None = None,
              inicio: datetime | None = None, fim: datetime | None = None, db: Session = Depends(db_dep)):
    return audit.listar(db, limit, offset, q, acao, usuario_id, entidade, instrumento_id, inicio, fim)


@router.get("/auditoria/{fonte}/{evento_id}")
def evento(fonte: str, evento_id: uuid.UUID, db: Session = Depends(db_dep)):
    result = audit.listar(db, fonte=fonte, evento_id=evento_id)
    if not result["items"]:
        raise HTTPException(404, "Evento nao encontrado.")
    return result["items"][0]


@router.post("/instrumentos/{instrumento_id}/exportacoes", status_code=202)
def solicitar_exportacao(instrumento_id: uuid.UUID, payload: ExportacaoIn, db: Session = Depends(db_dep)):
    return exports.serializar(exports.solicitar(db, instrumento_id, payload))


@router.get("/exportacoes")
def exportacoes(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                q: str = Query("", max_length=100), status: str | None = None,
                instrumento_id: uuid.UUID | None = None, db: Session = Depends(db_dep)):
    return exports.listar(db, limit, offset, q, status, instrumento_id)


@router.get("/exportacoes/{job_id}")
def exportacao(job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return exports.serializar(exports.obter(db, job_id))


@router.delete("/exportacoes/{job_id}")
def cancelar_exportacao(job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return exports.serializar(exports.cancelar(db, job_id))


@router.post("/exportacoes/{job_id}/repetir", status_code=202)
def repetir_exportacao(job_id: uuid.UUID, db: Session = Depends(db_dep)):
    return exports.serializar(exports.repetir(db, job_id))


@router.get("/exportacoes/{job_id}/download")
def download(job_id: uuid.UUID, db: Session = Depends(db_dep)):
    viewer_id = db.info["usuario"].id
    job, obj = exports.download(db, job_id)
    def stream():
        try:
            for chunk in obj["Body"].iter_chunks(chunk_size=1024 * 1024):
                # No long-lived signed URL: revocation also stops subsequent stream chunks.
                with SessionLocal() as check:
                    from app.models.user import Usuario
                    user = check.get(Usuario, viewer_id)
                    if not user or not user.ativo or user.excluido_em:
                        return
                    check.info["usuario"] = user
                    try:
                        current = exports.obter(check, job_id)
                        if current.status != "CONCLUIDA" or current.expira_em <= datetime.now(UTC):
                            return
                        exports._validar_base(check, current)
                    except HTTPException:
                        return
                yield chunk
        finally:
            obj["Body"].close()
    extension = "csv" if job.formato == "CSV" else "json"
    return StreamingResponse(stream(), media_type="text/csv" if extension == "csv" else "application/json",
        headers={"Content-Disposition": f'attachment; filename="exportacao-{job.id}.{extension}"',
                 "Content-Length": str(job.tamanho_bytes), "ETag": f'"{job.checksum}"',
                 "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/retencao/politicas")
def politicas(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), q: str = Query("", max_length=100),
              ativo: bool | None = None, categoria: str | None = None, db: Session = Depends(db_dep)):
    return retention.listar(db, limit, offset, q, ativo, categoria)


@router.get("/retencao/politicas/{politica_id}")
def politica(politica_id: uuid.UUID, db: Session = Depends(db_dep)):
    from app.models.instrumento import Instrumento
    row = retention.obter_politica(db, politica_id)
    instrument = db.get(Instrumento, row.instrumento_id) if row.instrumento_id else None
    return dict(retention.serializar(row), instrumento_nome=instrument.nome if instrument else None)


@router.post("/retencao/politicas", status_code=201)
def criar_politica(payload: PoliticaIn, db: Session = Depends(db_dep)):
    return retention.serializar(retention.salvar(db, payload))


@router.put("/retencao/politicas/{politica_id}")
def editar_politica(politica_id: uuid.UUID, payload: PoliticaIn, db: Session = Depends(db_dep)):
    return retention.serializar(retention.salvar(db, payload, politica_id))


@router.delete("/retencao/politicas/{politica_id}")
def desativar_politica(politica_id: uuid.UUID, db: Session = Depends(db_dep)):
    return retention.serializar(retention.desativar(db, politica_id))


@router.post("/retencao/politicas/{politica_id}/execucoes", status_code=202)
def solicitar_retencao(politica_id: uuid.UUID, payload: RetencaoIn, db: Session = Depends(db_dep)):
    return retention.serializar(retention.solicitar(db, politica_id, payload))


@router.get("/retencao/execucoes")
def execucoes(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
              politica_id: uuid.UUID | None = None, q: str = Query("", max_length=100), status: str | None = None,
              db: Session = Depends(db_dep)):
    return retention.listar_execucoes(db, limit, offset, politica_id, q, status)


@router.get("/retencao/execucoes/{execucao_id}")
def execucao(execucao_id: uuid.UUID, db: Session = Depends(db_dep)):
    job, policy = retention.obter_execucao(db, execucao_id)
    return dict(retention.serializar(job), instrumento_id=policy.instrumento_id)


@router.delete("/retencao/execucoes/{execucao_id}")
def cancelar_retencao(execucao_id: uuid.UUID, db: Session = Depends(db_dep)):
    return retention.serializar(retention.cancelar(db, execucao_id))


@router.post("/retencao/execucoes/{execucao_id}/repetir", status_code=202)
def repetir_retencao(execucao_id: uuid.UUID, db: Session = Depends(db_dep)):
    return retention.serializar(retention.repetir(db, execucao_id))


@router.put("/instrumentos/{instrumento_id}/registros/{registro_id}/retencao")
def impedimento(instrumento_id: uuid.UUID, registro_id: str, payload: ImpedimentoIn, db: Session = Depends(db_dep)):
    return retention.impedimento(db, instrumento_id, registro_id, payload)


@router.get("/relatorios")
def relatorios(inicio: datetime | None = None, fim: datetime | None = None,
               instrumento_id: uuid.UUID | None = None, db: Session = Depends(db_dep)):
    return resumo(db, inicio, fim, instrumento_id)


@router.get("/relatorios/registros")
def relatorio_registros(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                        instrumento_id: uuid.UUID | None = None, q: str = Query("", max_length=100),
                        db: Session = Depends(db_dep)):
    return registros_por_instrumento(db, limit, offset, instrumento_id, q)


@router.get("/relatorios/usuarios")
def relatorio_usuarios(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                       inicio: datetime | None = None, fim: datetime | None = None, db: Session = Depends(db_dep)):
    return alteracoes_usuarios(db, limit, offset, inicio, fim)


@router.get("/instrumentos/{instrumento_id}/registros/{registro_id}/retencao")
def ler_impedimento(instrumento_id: uuid.UUID, registro_id: str, db: Session = Depends(db_dep)):
    from app.models.editorial import EditorialRegistro
    from app.services.permissao_service import require
    require(db, "retencao_editar", instrumento_id)
    row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == instrumento_id,
                                                    EditorialRegistro.registro_id == registro_id))
    if not row:
        raise HTTPException(404, "Registro nao encontrado.")
    return {"bloqueado": row.retencao_bloqueada, "reter_ate": row.reter_ate,
            "expurgo_iniciado_em": row.expurgo_iniciado_em, "expurgado_em": row.expurgado_em}
