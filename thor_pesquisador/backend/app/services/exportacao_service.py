"""SQL is the durable queue. Checkpoints reference immutable private S3 chunks."""
import csv
import hashlib
import io
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from app.core.config import settings
from app.db.mongo import registros_collection, snapshots_collection
from app.db.session import SessionLocal
from app.models.conformidade import Exportacao, ExportacaoParte
from app.models.editorial import EditorialRegistro, PublicacaoImagem, PublicacaoInstrumento
from app.models.imagem import ImagemDocumento, RegistroImagem
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.models.user import Usuario
from app.services.armazenamento_service import armazenamento
from app.services.auditoria_service import registrar
from app.services.permissao_service import filtro_escopo, permissoes, require, require_any_scope

TRANSITIONS = {
    "PENDENTE": {"PROCESSANDO", "CANCELADA", "EXPIRADA"},
    "PROCESSANDO": {"CONCLUIDA", "FALHOU", "CANCELADA", "EXPIRADA"},
    "FALHOU": {"PENDENTE", "DESCARTADA", "EXPIRADA"},
    "CONCLUIDA": {"DESCARTADA", "EXPIRADA"},
    "CANCELADA": set(), "DESCARTADA": set(), "EXPIRADA": set(),
}


def transicionar(job, status):
    if status == job.status:
        return
    if status not in TRANSITIONS[job.status]:
        raise HTTPException(409, "Transicao de exportacao invalida.")
    job.status = status


def prefixo(job):
    return f"exportacoes/{job.id}/"


def serializar(job):
    fields = ("id", "usuario_id", "agente", "instrumento_id", "operacao_id", "formato", "escopo", "status",
              "processados", "partes", "tentativa", "checksum", "tamanho_bytes", "erro",
              "expira_em", "criado_em", "atualizado_em")
    return {key: getattr(job, key) for key in fields}


def _actor(db, job):
    user = db.get(Usuario, job.usuario_id, populate_existing=True)
    if not user or not user.ativo or user.excluido_em:
        raise HTTPException(403, "Solicitante inativo.")
    db.info["usuario"] = user
    require(db, "exportacoes_incluir", job.instrumento_id)
    require(db, "exportacoes_consultar", job.instrumento_id)
    require(db, "registros_consultar" if job.escopo == "ADMINISTRATIVO" else "consulta_publicada", job.instrumento_id)
    return user


def _validar_base(db, job):
    _actor(db, job)
    instrumento = db.get(Instrumento, job.instrumento_id, populate_existing=True)
    if not instrumento or instrumento.revisao_dados != job.revisao:
        raise HTTPException(409, "Dados alterados desde a solicitacao. Solicite nova exportacao.")
    if job.escopo == "PUBLICADO":
        from app.services.publicacao_service import publico
        publico(db, job.instrumento_id)
        if str(instrumento.publicacao_id) != job.parametros["publicacao_id"]:
            raise HTTPException(409, "Publicacao alterada.")
    return instrumento


def solicitar(db, iid, payload):
    user = require(db, "exportacoes_incluir", iid)
    require(db, "exportacoes_consultar", iid)
    require(db, "registros_consultar" if payload.escopo == "ADMINISTRATIVO" else "consulta_publicada", iid)
    existing = db.scalar(select(Exportacao).where(Exportacao.usuario_id == user.id,
                                                 Exportacao.operacao_id == payload.operacao_id))
    if existing:
        if (existing.instrumento_id, existing.formato, existing.escopo) != (iid, payload.formato, payload.escopo):
            raise HTTPException(409, "Operacao ja utilizada com outros parametros.")
        return existing
    # Serialize request IDs, including concurrent replays, without relying on Redis.
    db.execute(select(func.pg_advisory_xact_lock(int(payload.operacao_id.int % (2**63 - 1)))))
    existing = db.scalar(select(Exportacao).where(Exportacao.usuario_id == user.id,
                                                 Exportacao.operacao_id == payload.operacao_id))
    if existing:
        if (existing.instrumento_id, existing.formato, existing.escopo) != (iid, payload.formato, payload.escopo):
            raise HTTPException(409, "Operacao ja utilizada com outros parametros.")
        return existing
    instrumento = db.scalar(select(Instrumento).where(Instrumento.id == iid).with_for_update())
    if not instrumento:
        raise HTTPException(404, "Instrumento nao encontrado.")
    if payload.formato == "PACOTE" and payload.escopo != "PUBLICADO":
        raise HTTPException(422, "Pacote exige escopo publicado.")
    if payload.escopo == "PUBLICADO":
        from app.services.publicacao_service import campos_publicos, publico
        publico(db, iid)
        publication = db.get(PublicacaoInstrumento, instrumento.publicacao_id)
        fields = campos_publicos(db, publication.schema_json)
    else:
        fields = [{key: getattr(c, key) for key in ("chave", "nome", "tipo", "ordem")}
                  for c in db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == iid)
                                     .order_by(InstrumentoCampo.ordem, InstrumentoCampo.id))]
    now = datetime.now(UTC)
    job = Exportacao(id=uuid.uuid4(), usuario_id=user.id, agente=user.nome, instrumento_id=iid,
        operacao_id=payload.operacao_id, formato=payload.formato, escopo=payload.escopo,
        revisao=instrumento.revisao_dados, schema_json={"instrumento_id": str(iid), "nome": instrumento.nome,
        "schema_version": instrumento.schema_version, "campos": fields}, parametros={
            "publicacao_id": str(instrumento.publicacao_id), "corte_em": now.isoformat(),
            "consistencia": "revisao otimista: qualquer alteracao invalida o arquivo"},
        expira_em=now + timedelta(hours=settings.exportacao_validade_horas))
    db.add(job)
    registrar(db, "SOLICITAR_EXPORTACAO", "exportacao", job.id, iid,
              detalhe={"escopo": job.escopo, "formato": job.formato}, operacao_id=payload.operacao_id)
    db.commit()
    return job


def listar(db, limit, offset, q="", status=None, instrumento_id=None):
    user = db.info["usuario"]
    require_any_scope(db, "exportacoes_consultar")
    filters = [filtro_escopo(db, Exportacao.instrumento_id, "exportacoes_consultar")]
    if "*" not in permissoes(db):
        filters.append(Exportacao.usuario_id == user.id)
    if status:
        filters.append(Exportacao.status == status)
    if instrumento_id:
        filters.append(Exportacao.instrumento_id == instrumento_id)
    if q:
        filters.append(or_(Exportacao.formato.ilike("%" + q[:100] + "%"), Exportacao.status.ilike("%" + q[:100] + "%")))
    return {"items": [serializar(j) for j in db.scalars(select(Exportacao).where(*filters)
             .order_by(Exportacao.criado_em.desc(), Exportacao.id).limit(limit).offset(offset))],
            "total": db.scalar(select(func.count()).select_from(Exportacao).where(*filters))}


def obter(db, jid, acao="exportacoes_consultar", lock=False):
    job = db.scalar(select(Exportacao).where(Exportacao.id == jid).with_for_update() if lock
                    else select(Exportacao).where(Exportacao.id == jid))
    if not job:
        raise HTTPException(404, "Exportacao nao encontrada.")
    user = require(db, acao, job.instrumento_id)
    if job.usuario_id != user.id and "*" not in permissoes(db):
        raise HTTPException(403, "Exportacao de outro usuario.")
    return job


def cancelar(db, jid):
    job = obter(db, jid, "exportacoes_excluir", lock=True)
    if job.status in {"CANCELADA", "DESCARTADA", "EXPIRADA"}:
        return job
    transicionar(job, "CANCELADA" if job.status in {"PENDENTE", "PROCESSANDO"} else "DESCARTADA")
    job.lease_token, job.lease_ate = None, None
    registrar(db, "CANCELAR_EXPORTACAO", "exportacao", job.id, job.instrumento_id,
              detalhe={"status": job.status}, operacao_id=job.operacao_id)
    db.commit()
    return job


def repetir(db, jid):
    job = obter(db, jid, "exportacoes_repetir", lock=True)
    if job.status == "PENDENTE":
        return job
    if job.status != "FALHOU" or job.expira_em <= datetime.now(UTC):
        raise HTTPException(409, "Somente falhas nao expiradas podem ser repetidas.")
    _validar_base(db, job)
    transicionar(job, "PENDENTE")
    job.tentativa += 1
    job.erro = None
    job.lease_token, job.lease_ate = None, None
    registrar(db, "REPETIR_EXPORTACAO", "exportacao", job.id, job.instrumento_id,
              detalhe={"tentativa": job.tentativa}, operacao_id=job.operacao_id)
    db.commit()
    return job


def csv_value(value):
    if isinstance(value, str):
        if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
            return "'" + value
        return value
    return json.dumps(value, ensure_ascii=False, default=str) if isinstance(value, (list, dict, bool)) else value


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str, allow_nan=False).encode("utf-8")


def _referencias(db, job, docs):
    if job.formato != "PACOTE":
        return
    # No object keys, external URIs, signed URLs or image metadata in portable packages.
    snapshots = [d.get("snapshot_id") for d in docs]
    rows = db.execute(select(PublicacaoImagem.snapshot_id, ImagemDocumento.id, ImagemDocumento.titulo,
                            ImagemDocumento.mime_type, ImagemDocumento.checksum_sha256)
        .join(ImagemDocumento).where(PublicacaoImagem.snapshot_id.in_(snapshots),
            ImagemDocumento.direitos_acesso == "PUBLICO").order_by(ImagemDocumento.id)
            .limit(settings.exportacao_max_referencias_lote + 1))
    refs = {}
    for index, (sid, iid, title, mime, checksum) in enumerate(rows):
        if index >= settings.exportacao_max_referencias_lote:
            raise HTTPException(422, "Lote excede o limite de referencias. Reduza o tamanho do lote.")
        refs.setdefault(sid, []).append({"id": str(iid), "titulo": title, "mime_type": mime,
            "checksum_sha256": checksum, "conteudo": f"/api/v1/imagens/{iid}/conteudo"})
    for doc in docs:
        doc["imagens"] = refs.get(doc.get("snapshot_id"), [])


def _lote(db, job):
    size = settings.exportacao_batch_size
    keys = {c["chave"] for c in job.schema_json["campos"]}
    docs = []
    if job.escopo == "ADMINISTRATIVO":
        query = {"instrumento_id": str(job.instrumento_id), "status": {"$ne": "EXCLUIDO"}}
        if job.checkpoint:
            query["_id"] = {"$gt": job.checkpoint}
        budget, canonical = 0, {}
        for doc in registros_collection().find(query).sort("_id", 1).limit(size).batch_size(1):
            canonical[doc["_id"]] = (doc.get("_revision", 1), doc.get("status", "ATIVO"))
            docs.append({"id": doc["_id"], "versao": doc.get("_revision", 1),
                         "dados": {k: v for k, v in doc.get("dados", {}).items() if k in keys}})
            budget += len(_bytes(docs[-1]))
            if budget >= 8 * 1024 * 1024:
                break
        controls = list(db.scalars(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == job.instrumento_id,
                                   EditorialRegistro.registro_id.in_(canonical))))
        if len(controls) != len(canonical):
            raise HTTPException(409, "Registro sem controle SQL; reconciliacao necessaria.")
        for control in controls:
            if canonical[control.registro_id] != (control.versao, control.status_operacional):
                raise HTTPException(409, "Registro necessita reconciliacao.")
    else:
        query = select(EditorialRegistro).where(EditorialRegistro.instrumento_id == job.instrumento_id,
            EditorialRegistro.status_operacional == "ATIVO", EditorialRegistro.status_editorial != "ARQUIVADO",
            EditorialRegistro.snapshot_id.is_not(None))
        if job.checkpoint:
            query = query.where(EditorialRegistro.registro_id > job.checkpoint)
        rows = list(db.scalars(query.order_by(EditorialRegistro.registro_id).limit(size)))
        by_snapshot = {r.snapshot_id: r for r in rows}
        budget, snapshots = 0, []
        for snap in snapshots_collection().find({"_id": {"$in": list(by_snapshot)}}, {"imagens": 0}).sort("registro_id", 1).batch_size(1):
            row = by_snapshot[snap["_id"]]
            if row.registro_id != rows[len(snapshots)].registro_id:
                raise HTTPException(409, "Snapshot publicado indisponivel.")
            snapshots.append(snap)
            budget += len(_bytes(snap.get("dados", {})))
            if budget >= 8 * 1024 * 1024:
                break
        if rows and (not snapshots or (budget < 8 * 1024 * 1024 and len(snapshots) != len(rows))):
            raise HTTPException(409, "Snapshot publicado indisponivel.")
        schemas = {str(s.id): s for s in db.scalars(select(PublicacaoInstrumento).where(
            PublicacaoInstrumento.id.in_([uuid.UUID(s["schema_id"]) for s in snapshots])))}
        for snap in snapshots:
            row = by_snapshot[snap["_id"]]
            schema = schemas.get(snap["schema_id"])
            allowed = keys & {c["chave"] for c in schema.schema_json["campos"] if c.get("exibir_publico")} if schema else set()
            docs.append({"id": row.registro_id, "snapshot_id": row.snapshot_id, "versao": snap["versao"],
                         "dados": {k: v for k, v in snap["dados"].items() if k in allowed}})
        _referencias(db, job, docs)
    return docs


def _codificar(job, docs):
    if job.formato != "CSV":
        return b",".join(_bytes(d) for d in docs)
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    for doc in docs:
        writer.writerow([doc["id"], doc["versao"]] + [csv_value(doc["dados"].get(c["chave"]))
                         for c in job.schema_json["campos"]])
    return output.getvalue().encode("utf-8")


def _lease(db, jid, token, lock=False):
    db.expire_all()
    query = select(Exportacao).where(Exportacao.id == jid)
    job = db.scalar(query.with_for_update() if lock else query)
    if job.status != "PROCESSANDO" or job.lease_token != token or job.lease_ate <= datetime.now(UTC):
        raise HTTPException(409, "Lease perdida ou exportacao cancelada.")
    if job.expira_em <= datetime.now(UTC):
        raise HTTPException(410, "Exportacao expirada.")
    _validar_base(db, job)
    return job


def processar_pendente(db):
    now = datetime.now(UTC)
    job = db.scalar(select(Exportacao).where(or_(Exportacao.status == "PENDENTE",
        (Exportacao.status == "PROCESSANDO") & (Exportacao.lease_ate < now)))
        .order_by(Exportacao.criado_em).with_for_update(skip_locked=True).limit(1))
    if not job:
        return False
    jid, token = job.id, uuid.uuid4()
    if job.expira_em <= now:
        transicionar(job, "EXPIRADA")
        db.commit()
        return True
    transicionar(job, "PROCESSANDO")
    job.lease_token, job.lease_ate = token, now + timedelta(seconds=settings.jobs_lease_segundos)
    db.commit()
    final_key = None
    try:
        while True:
            job = _lease(db, jid, token)
            docs = _lote(db, job)
            if not docs:
                break
            number = job.partes + 1
            key = prefixo(job) + f"chunks/{number}-{token}"
            data = _codificar(job, docs)
            armazenamento.salvar_upload(key, data, "application/octet-stream")
            job = _lease(db, jid, token, lock=True)
            db.add(ExportacaoParte(job_id=jid, numero=number, object_key=key,
                                  checksum=hashlib.sha256(data).hexdigest(), quantidade=len(docs)))
            job.partes, job.checkpoint = number, docs[-1]["id"]
            job.processados += len(docs)
            job.lease_ate = datetime.now(UTC) + timedelta(seconds=settings.jobs_lease_segundos)
            db.commit()

        def heartbeat():
            current = _lease(db, jid, token, lock=True)
            current.lease_ate = datetime.now(UTC) + timedelta(seconds=settings.jobs_lease_segundos)
            db.commit()

        def chunks():
            if job.formato == "CSV":
                output = io.StringIO(newline="")
                csv.writer(output).writerow(["id", "versao"] + [csv_value(c["chave"]) for c in job.schema_json["campos"]])
                yield output.getvalue().encode()
            else:
                yield b'{"manifesto":' + _bytes(dict(job.parametros, revisao=job.revisao, total=job.processados)) + b',"schema":' + _bytes(job.schema_json) + b',"registros":['
            for number in range(1, job.partes + 1):
                heartbeat()
                part = db.get(ExportacaoParte, (jid, number))
                obj = armazenamento.obter_objeto(part.object_key)["Body"]
                digest = hashlib.sha256()
                if number > 1 and job.formato != "CSV":
                    yield b","
                try:
                    for chunk in obj.iter_chunks(chunk_size=1024 * 1024):
                        digest.update(chunk)
                        yield chunk
                finally:
                    obj.close()
                if digest.hexdigest() != part.checksum:
                    raise RuntimeError("Checksum de checkpoint invalido.")
            if job.formato != "CSV":
                yield b"]}"

        final_key = prefixo(job) + f"resultado/{token}"
        mime = "text/csv; charset=utf-8" if job.formato == "CSV" else "application/json"
        checksum, size = armazenamento.salvar_fluxo(final_key, chunks(), mime, heartbeat)
        job = _lease(db, jid, token, lock=True)
        transicionar(job, "CONCLUIDA")
        job.object_key, job.checksum, job.tamanho_bytes = final_key, checksum, size
        job.lease_token, job.lease_ate = None, None
        registrar(db, "CONCLUIR_EXPORTACAO", "exportacao", jid, job.instrumento_id,
                  detalhe={"processados": job.processados, "executor": "export_worker"}, operacao_id=job.operacao_id)
        db.commit()
    except Exception as exc:
        logging.getLogger("thor.jobs").warning(json.dumps({"evento": "EXPORTACAO_FALHOU", "job_id": str(jid),
            "erro_tipo": type(exc).__name__}))
        db.rollback()
        job = db.scalar(select(Exportacao).where(Exportacao.id == jid).with_for_update())
        if job.status == "PROCESSANDO" and job.lease_token == token:
            transicionar(job, "EXPIRADA" if job.expira_em <= datetime.now(UTC) else "FALHOU")
            job.erro = "Dados ou permissoes alterados." if isinstance(exc, HTTPException) and exc.status_code in {403, 404, 409} else "Falha de processamento. Consulte o request_id nos logs tecnicos."
            job.lease_token, job.lease_ate = None, None
            user = db.get(Usuario, job.usuario_id)
            registrar(db, "FALHAR_EXPORTACAO", "exportacao", jid, job.instrumento_id, usuario=user,
                      detalhe={"status": job.status, "executor": "export_worker"}, operacao_id=job.operacao_id)
            db.commit()
        if final_key:
            try:
                armazenamento.remover_objeto(final_key)
            except Exception:
                pass  # Retention retries prefix cleanup; no download is exposed.
    return True


def download(db, jid):
    job = obter(db, jid)
    actor = db.info["usuario"]
    if job.status != "CONCLUIDA" or job.expira_em <= datetime.now(UTC) or not job.object_key:
        raise HTTPException(410, "Arquivo indisponivel ou expirado.")
    _validar_base(db, job)
    db.info["usuario"] = actor
    require(db, "exportacoes_consultar", job.instrumento_id)
    obj = armazenamento.obter_objeto(job.object_key)
    registrar(db, "DOWNLOAD_EXPORTACAO", "exportacao", jid, job.instrumento_id)
    db.commit()
    return job, obj
