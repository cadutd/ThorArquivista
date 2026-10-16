"""Explicit policies; immutable history, snapshots and shared images are never deleted."""
import uuid
import json
import logging
from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from app.core.config import settings
from app.db.mongo import registros_collection, snapshots_collection
from app.models.conformidade import ExecucaoRetencao, Exportacao, LogRequisicao, PoliticaRetencao
from app.models.editorial import EditorialRegistro
from app.models.instrumento import Instrumento
from app.models.user import Sessao, Usuario
from app.services.armazenamento_service import armazenamento
from app.services.auditoria_service import registrar
from app.services.permissao_service import filtro_escopo, permissoes, require, require_any_scope

TRANSITIONS = {"PENDENTE": {"PROCESSANDO", "CANCELADA"}, "PROCESSANDO": {"CONCLUIDA", "FALHOU", "CANCELADA"},
               "FALHOU": {"PENDENTE"}, "CONCLUIDA": set(), "CANCELADA": set()}


def transicionar(job, status):
    if job.status == status:
        return
    if status not in TRANSITIONS[job.status]:
        raise HTTPException(409, "Transicao de retencao invalida.")
    job.status = status


def serializar(row):
    return {c.name: getattr(row, c.name) for c in row.__table__.columns if c.name not in {"lease_token", "lease_ate"}}


def obter_politica(db, pid, acao="retencao_consultar", lock=False):
    query = select(PoliticaRetencao).where(PoliticaRetencao.id == pid)
    row = db.scalar(query.with_for_update() if lock else query)
    if not row:
        raise HTTPException(404, "Politica nao encontrada.")
    require(db, acao, row.instrumento_id)
    return row


def listar(db, limit, offset, q="", ativo=None, categoria=None):
    require_any_scope(db, "retencao_consultar")
    filters = [filtro_escopo(db, PoliticaRetencao.instrumento_id, "retencao_consultar")]
    if q:
        filters.append(PoliticaRetencao.nome.ilike("%" + q[:100] + "%"))
    if ativo is not None:
        filters.append(PoliticaRetencao.ativo == ativo)
    if categoria:
        filters.append(PoliticaRetencao.categoria == categoria)
    return {"items": [serializar(p) for p in db.scalars(select(PoliticaRetencao).where(*filters)
            .order_by(PoliticaRetencao.nome, PoliticaRetencao.id).limit(limit).offset(offset))],
            "total": db.scalar(select(func.count()).select_from(PoliticaRetencao).where(*filters))}


def salvar(db, payload, pid=None):
    require(db, "retencao_editar" if pid else "retencao_incluir", payload.instrumento_id)
    if payload.instrumento_id and not db.get(Instrumento, payload.instrumento_id):
        raise HTTPException(422, "Instrumento inexistente.")
    row = obter_politica(db, pid, "retencao_editar", lock=True) if pid else PoliticaRetencao(id=uuid.uuid4())
    if pid and db.scalar(select(ExecucaoRetencao.id).where(ExecucaoRetencao.politica_id == pid,
                       ExecucaoRetencao.status.in_(["PENDENTE", "PROCESSANDO"])).limit(1)):
        raise HTTPException(409, "Cancele ou conclua a execucao antes de alterar a politica.")
    if pid and (payload.categoria != row.categoria or payload.instrumento_id != row.instrumento_id):
        raise HTTPException(409, "Categoria e instrumento nao podem ser alterados. Crie outra politica.")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Nome de politica ja utilizado.") from exc
    return row


def desativar(db, pid):
    row = obter_politica(db, pid, "retencao_excluir", lock=True)
    if db.scalar(select(ExecucaoRetencao.id).where(ExecucaoRetencao.politica_id == pid,
                 ExecucaoRetencao.status.in_(["PENDENTE", "PROCESSANDO"])).limit(1)):
        raise HTTPException(409, "Cancele as execucoes antes de desativar a politica.")
    row.ativo = False
    db.commit()
    return row


def solicitar(db, pid, payload):
    db.execute(select(func.pg_advisory_xact_lock(int(payload.operacao_id.int % (2**63 - 1)))))
    policy = obter_politica(db, pid, "retencao_simular" if payload.simulacao else "retencao_executar", lock=True)
    user = db.info["usuario"]
    existing = db.scalar(select(ExecucaoRetencao).where(ExecucaoRetencao.usuario_id == user.id,
                                                       ExecucaoRetencao.operacao_id == payload.operacao_id))
    if existing:
        if existing.politica_id != pid or existing.simulacao != payload.simulacao:
            raise HTTPException(409, "Operacao ja utilizada.")
        return existing
    if not policy.ativo or policy.bloqueada or (not payload.simulacao and not policy.permitir_expurgo):
        raise HTTPException(409, "Politica inativa, bloqueada ou sem autorizacao de expurgo.")
    if db.scalar(select(ExecucaoRetencao.id).where(ExecucaoRetencao.politica_id == pid,
                 ExecucaoRetencao.status.in_(["PENDENTE", "PROCESSANDO"])).limit(1)):
        raise HTTPException(409, "Ja existe execucao pendente para esta politica.")
    job = ExecucaoRetencao(id=uuid.uuid4(), politica_id=pid, usuario_id=user.id, agente=user.nome,
        operacao_id=payload.operacao_id, simulacao=payload.simulacao, status="PENDENTE",
        corte_em=datetime.now(UTC) - timedelta(days=policy.dias))
    db.add(job)
    registrar(db, "SOLICITAR_RETENCAO", "retencao", job.id, policy.instrumento_id,
              detalhe={"simulacao": payload.simulacao, "categoria": policy.categoria}, operacao_id=job.operacao_id)
    db.commit()
    return job


def obter_execucao(db, jid, acao=None, lock=False):
    query = select(ExecucaoRetencao).where(ExecucaoRetencao.id == jid)
    job = db.scalar(query.with_for_update() if lock else query)
    if not job:
        raise HTTPException(404, "Execucao nao encontrada.")
    policy = obter_politica(db, job.politica_id, acao or "retencao_consultar")
    if job.usuario_id != db.info["usuario"].id and "*" not in permissoes(db):
        raise HTTPException(403, "Execucao de outro usuario.")
    return job, policy


def listar_execucoes(db, limit, offset, politica_id=None, q="", status=None):
    require_any_scope(db, "retencao_consultar")
    filters = [filtro_escopo(db, PoliticaRetencao.instrumento_id, "retencao_consultar")]
    if "*" not in permissoes(db):
        filters.append(ExecucaoRetencao.usuario_id == db.info["usuario"].id)
    if politica_id:
        filters.append(ExecucaoRetencao.politica_id == politica_id)
    if status:
        filters.append(ExecucaoRetencao.status == status)
    if q:
        filters.append(or_(ExecucaoRetencao.agente.ilike("%" + q[:100] + "%"),
                           ExecucaoRetencao.status.ilike("%" + q[:100] + "%")))
    query = select(ExecucaoRetencao).join(PoliticaRetencao, PoliticaRetencao.id == ExecucaoRetencao.politica_id).where(*filters)
    return {"items": [dict(serializar(j), instrumento_id=iid) for j, iid in db.execute(
            query.add_columns(PoliticaRetencao.instrumento_id).order_by(ExecucaoRetencao.criado_em.desc(),
            ExecucaoRetencao.id).limit(limit).offset(offset))],
            "total": db.scalar(select(func.count()).select_from(query.subquery()))}


def cancelar(db, jid):
    job, policy = obter_execucao(db, jid, "retencao_cancelar", lock=True)
    if job.status == "CANCELADA":
        return job
    transicionar(job, "CANCELADA")
    job.lease_token, job.lease_ate = None, None
    registrar(db, "CANCELAR_RETENCAO", "retencao", job.id, policy.instrumento_id, operacao_id=job.operacao_id)
    db.commit()
    return job


def repetir(db, jid):
    job, policy = obter_execucao(db, jid, lock=True)
    require(db, "retencao_simular" if job.simulacao else "retencao_executar", policy.instrumento_id)
    db.refresh(policy, with_for_update=True)
    if job.status == "PENDENTE":
        return job
    transicionar(job, "PENDENTE")
    if not policy.ativo or policy.bloqueada or (not job.simulacao and not policy.permitir_expurgo):
        raise HTTPException(409, "Politica indisponivel.")
    if db.scalar(select(ExecucaoRetencao.id).where(ExecucaoRetencao.politica_id == policy.id,
        ExecucaoRetencao.id != jid, ExecucaoRetencao.status.in_(["PENDENTE", "PROCESSANDO"])).limit(1)):
        raise HTTPException(409, "Ja existe execucao pendente para esta politica.")
    job.erro, job.lease_token, job.lease_ate = None, None, None
    registrar(db, "REPETIR_RETENCAO", "retencao", job.id, policy.instrumento_id, operacao_id=job.operacao_id)
    db.commit()
    return job


def impedimento(db, iid, rid, payload):
    user = require(db, "retencao_editar", iid)
    db.scalar(select(Instrumento).where(Instrumento.id == iid).with_for_update())
    row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == iid,
                                                    EditorialRegistro.registro_id == rid).with_for_update())
    if not row:
        raise HTTPException(404, "Registro nao encontrado.")
    if row.expurgo_iniciado_em:
        raise HTTPException(409, "Expurgo ja iniciado; nao e possivel alterar a retencao.")
    row.retencao_bloqueada, row.reter_ate = payload.bloqueado, payload.reter_ate
    registrar(db, "IMPEDIMENTO_RETENCAO", "registro", rid, iid, rid,
              {"bloqueados": int(payload.bloqueado)}, usuario=user)
    db.commit()
    return {"bloqueado": row.retencao_bloqueada, "reter_ate": row.reter_ate}


def _elegivel(row, now):
    return (row.status_operacional == "EXCLUIDO" and not row.snapshot_id and not row.versao_publicada
        and not row.retencao_bloqueada and (not row.reter_ate or row.reter_ate <= now)
        and not snapshots_collection().find_one({"instrumento_id": str(row.instrumento_id),
                                                "registro_id": row.registro_id}, {"_id": 1}))


def _batch(db, job, policy):
    size = settings.retencao_batch_size
    if policy.categoria == "REGISTRO_EXCLUIDO":
        model, date = EditorialRegistro, EditorialRegistro.atualizado_em
        filters = [model.instrumento_id == policy.instrumento_id, model.status_operacional == "EXCLUIDO",
                   model.expurgado_em.is_(None), or_(date < job.corte_em, model.expurgo_iniciado_em.is_not(None))]
    elif policy.categoria == "SESSAO":
        model, filters = Sessao, [Sessao.expira_em < job.corte_em]
    elif policy.categoria == "EXPORTACAO":
        model = Exportacao
        filters = [model.expira_em < job.corte_em, model.status != "PROCESSANDO"]
    else:
        model = LogRequisicao
        filters = [model.categoria == policy.categoria, model.criado_em < job.corte_em]
    if job.checkpoint:
        filters.append(model.id > uuid.UUID(job.checkpoint))
    return list(db.scalars(select(model).where(*filters).order_by(model.id).with_for_update(skip_locked=True).limit(size)))


def _remover(db, job, policy, row):
    if isinstance(row, EditorialRegistro):
        # Lock matches editorial mutations; keep the SQL tombstone and every historical event.
        db.scalar(select(Instrumento).where(Instrumento.id == row.instrumento_id).with_for_update())
        db.refresh(row, with_for_update=True)
        if not _elegivel(row, datetime.now(UTC)):
            return False
        if not row.expurgo_iniciado_em:
            token = job.lease_token
            row.expurgo_iniciado_em = datetime.now(UTC)
            registrar(db, "EXPURGO_INTENCAO", "registro", row.registro_id, row.instrumento_id,
                      row.registro_id, {"etapa": "INTENCAO_PERSISTIDA"}, operacao_id=job.operacao_id)
            db.commit()
            db.refresh(job, with_for_update=True)
            if job.status != "PROCESSANDO" or job.lease_token != token or job.lease_ate <= datetime.now(UTC):
                raise HTTPException(409, "Execucao cancelada ou lease perdida.")
            user = db.get(Usuario, job.usuario_id, populate_existing=True)
            if not user or not user.ativo or user.excluido_em:
                raise HTTPException(403, "Solicitante inativo.")
            db.info["usuario"] = user
            require(db, "retencao_executar", policy.instrumento_id)
            db.refresh(policy, with_for_update=True)
            if not policy.ativo or policy.bloqueada or not policy.permitir_expurgo:
                raise HTTPException(409, "Politica indisponivel.")
            db.scalar(select(Instrumento).where(Instrumento.id == row.instrumento_id).with_for_update())
            db.refresh(row, with_for_update=True)
            if not _elegivel(row, datetime.now(UTC)):
                return False
        registros_collection().delete_one({"_id": row.registro_id, "instrumento_id": str(row.instrumento_id),
                                           "status": "EXCLUIDO"})
        if registros_collection().find_one({"_id": row.registro_id, "instrumento_id": str(row.instrumento_id)}):
            raise RuntimeError("Estado canonico inconsistente; expurgo interrompido.")
        from app.services.imagem_service import limpar_vinculos
        from app.services.indexacao_service import _meili_request, indice_nome
        from app.services.publicacao_service import aguardar
        limpar_vinculos(db, row.instrumento_id, row.registro_id, job.usuario_id)
        aguardar(_meili_request("DELETE", f"/indexes/{indice_nome(row.instrumento_id)}/documents/{row.registro_id}",
                               allow_not_found=True))
        row.expurgado_em = datetime.now(UTC)
        registrar(db, "EXPURGO_CONCLUIDO", "registro", row.registro_id, row.instrumento_id, row.registro_id,
                  {"etapa": "CONCLUIDA"}, operacao_id=job.operacao_id)
    elif isinstance(row, Exportacao):
        armazenamento.limpar_prefixo(f"exportacoes/{row.id}/")
        from app.services.exportacao_service import transicionar
        if row.status not in {"EXPIRADA", "CANCELADA", "DESCARTADA"}:
            transicionar(row, "EXPIRADA")
        row.object_key = None
    else:
        db.delete(row)
    return True


def processar_pendente(db):
    now = datetime.now(UTC)
    job = db.scalar(select(ExecucaoRetencao).where(or_(ExecucaoRetencao.status == "PENDENTE",
        (ExecucaoRetencao.status == "PROCESSANDO") & (ExecucaoRetencao.lease_ate < now)))
        .order_by(ExecucaoRetencao.criado_em).with_for_update(skip_locked=True).limit(1))
    if not job:
        return False
    jid, token = job.id, uuid.uuid4()
    transicionar(job, "PROCESSANDO")
    job.lease_token, job.lease_ate = token, now + timedelta(seconds=settings.jobs_lease_segundos)
    db.commit()
    try:
        # One bounded batch per claim; other policies and cancellation are not starved.
        db.expire_all()
        job = db.scalar(select(ExecucaoRetencao).where(ExecucaoRetencao.id == jid).with_for_update())
        if job.lease_token != token or job.status != "PROCESSANDO":
            return True
        user = db.get(Usuario, job.usuario_id, populate_existing=True)
        if not user or not user.ativo or user.excluido_em:
            raise HTTPException(403, "Solicitante inativo.")
        db.info["usuario"] = user
        policy = obter_politica(db, job.politica_id, "retencao_simular" if job.simulacao else "retencao_executar", lock=True)
        if not policy.ativo or policy.bloqueada or (not job.simulacao and not policy.permitir_expurgo):
            raise HTTPException(409, "Politica indisponivel.")
        rows = _batch(db, job, policy)
        for row in rows:
            user = db.get(Usuario, job.usuario_id, populate_existing=True)
            if not user or not user.ativo or user.excluido_em:
                raise HTTPException(403, "Solicitante inativo.")
            db.info["usuario"] = user
            require(db, "retencao_simular" if job.simulacao else "retencao_executar", policy.instrumento_id)
            db.refresh(policy, with_for_update=True)
            if not policy.ativo or policy.bloqueada or (not job.simulacao and not policy.permitir_expurgo):
                raise HTTPException(409, "Politica indisponivel.")
            eligible = _elegivel(row, datetime.now(UTC)) if isinstance(row, EditorialRegistro) else True
            if eligible and not job.simulacao:
                removed = _remover(db, job, policy, row)
                job.removidos += int(removed)
                eligible = bool(removed)
            job.processados += 1
            job.elegiveis += int(eligible)
            job.bloqueados += int(not eligible)
            job.checkpoint = str(row.id)
            job.lease_ate = datetime.now(UTC) + timedelta(seconds=settings.jobs_lease_segundos)
            db.commit()
            db.refresh(job, with_for_update=True)
            if job.status != "PROCESSANDO" or job.lease_token != token:
                return True
        if len(rows) < settings.retencao_batch_size:
            transicionar(job, "CONCLUIDA")
            registrar(db, "CONCLUIR_RETENCAO", "retencao", jid, policy.instrumento_id,
                detalhe={"processados": job.processados, "elegiveis": job.elegiveis, "bloqueados": job.bloqueados,
                         "removidos": job.removidos, "simulacao": job.simulacao, "executor": "retention_worker"},
                operacao_id=job.operacao_id)
            job.lease_token, job.lease_ate = None, None
        else:
            # Keep PROCESSANDO but relinquish the lease so the next bounded batch can claim it.
            job.lease_ate = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    except Exception as exc:
        logging.getLogger("thor.jobs").warning(json.dumps({"evento": "RETENCAO_FALHOU", "job_id": str(jid),
            "erro_tipo": type(exc).__name__}))
        db.rollback()
        job = db.scalar(select(ExecucaoRetencao).where(ExecucaoRetencao.id == jid).with_for_update())
        if job.status == "PROCESSANDO" and job.lease_token == token:
            transicionar(job, "FALHOU")
            job.erro = "Execucao interrompida. Revise permissoes, politica e servicos antes de repetir."
            job.lease_token, job.lease_ate = None, None
            registrar(db, "FALHAR_RETENCAO", "retencao", jid,
                      usuario=db.get(Usuario, job.usuario_id), operacao_id=job.operacao_id)
            db.commit()
    return True


def expirar_exportacoes(db, limit=100):
    now = datetime.now(UTC)
    rows = list(db.scalars(select(Exportacao).where(Exportacao.expira_em <= now,
        Exportacao.status.in_(["PENDENTE", "PROCESSANDO", "CONCLUIDA", "FALHOU"]))
        .order_by(Exportacao.expira_em).with_for_update(skip_locked=True).limit(limit)))
    from app.services.exportacao_service import transicionar
    for job in rows:
        transicionar(job, "EXPIRADA")
        job.lease_token, job.lease_ate = None, None
        registrar(db, "EXPIRAR_EXPORTACAO", "exportacao", job.id, job.instrumento_id,
                  usuario=db.get(Usuario, job.usuario_id), detalhe={"executor": "retention_worker"})
    db.commit()
    return len(rows)


def limpar_artefatos(db, limit=100):
    # Revisit terminal prefixes: an in-flight cancelled writer may finish after first cleanup.
    rows = list(db.scalars(select(Exportacao).where(Exportacao.status.in_(["EXPIRADA", "CANCELADA", "DESCARTADA"]))
        .order_by(Exportacao.ultimo_descarte_em.asc().nulls_first(), Exportacao.id)
        .with_for_update(skip_locked=True).limit(limit)))
    removed = 0
    for job in rows:
        try:
            deleted = armazenamento.limpar_prefixo(f"exportacoes/{job.id}/")
            first_cleanup = job.ultimo_descarte_em is None
            job.object_key = None
            job.ultimo_descarte_em = datetime.now(UTC)
            removed += 1
            if first_cleanup or deleted:
                registrar(db, "LIMPAR_ARQUIVOS_EXPORTACAO", "exportacao", job.id, job.instrumento_id,
                    usuario=db.get(Usuario, job.usuario_id), detalhe={"executor": "retention_worker"})
            db.commit()
        except Exception:
            db.rollback()
            # No successful cleanup marker: next run retries the same prefix.
    return removed
