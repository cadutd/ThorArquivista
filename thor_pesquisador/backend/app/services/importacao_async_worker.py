"""Lease-fenced import phases with disk-backed source streaming and bounded S3 shards."""
import hashlib
import json
import logging
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from app.core.config import settings
from app.models.importacao_async import ImportacaoAsync as Job, ImportacaoAsyncParte as Parte
from app.models.instrumento import Instrumento, IndexacaoJob
from app.models.user import Usuario
from app.schemas.importacao import ConfiguracaoImportacao
from app.services import importacao_async_service as service
from app.services.armazenamento_service import armazenamento
from app.services.auditoria_service import registrar
from app.services.importacao_arquivo import converter, sugerir_tipo, chave_sugerida
from app.services.registro_service import _validar
from app.services.indexacao_service import enqueue_indexacao


def verificar(db, jid, token, lock=False):
    db.expire_all()
    query = select(Job).where(Job.id == jid)
    job = db.scalar(query.with_for_update() if lock else query)
    if job.status != job.phase or job.lease_token != token or job.lease_ate <= datetime.now(UTC):
        raise HTTPException(409, "Execucao cancelada ou lease perdida.")
    if job.expira_em <= datetime.now(UTC):
        raise HTTPException(410, "Arquivo expirado.")
    actor = db.get(Usuario, job.usuario_id)
    if not actor or not actor.ativo or actor.excluido_em is not None:
        raise HTTPException(403, "Usuario inativo.")
    db.info["usuario"] = actor
    instrument = service.instrumento(db, job.instrumento_id)
    if job.phase in {"VALIDANDO", "IMPORTANDO"} and instrument.schema_version != job.schema_version:
        raise HTTPException(409, "Schema alterado.")
    job.lease_ate = datetime.now(UTC) + timedelta(seconds=settings.jobs_lease_segundos)
    return job


def heartbeat(db, jid, token, count=None):
    job = verificar(db, jid, token, lock=True)
    if count is not None:
        job.fase_processados = count
    db.commit()


@contextmanager
def fonte(db, job, token):
    jid = job.id
    parts = list(db.scalars(select(Parte).where(Parte.job_id == jid, Parte.categoria == "FONTE").order_by(Parte.numero)))
    descriptors = [(p.object_key, p.checksum, p.tamanho_bytes) for p in parts]
    total, digest, last = 0, hashlib.sha256(), time.monotonic()
    with tempfile.NamedTemporaryFile(prefix="thor-import-", suffix="." + job.formato) as temporary:
        for key, expected, expected_size in descriptors:
            heartbeat(db, jid, token)
            body = armazenamento.obter_objeto(key)["Body"]
            part_hash, part_size = hashlib.sha256(), 0
            try:
                for chunk in body.iter_chunks(chunk_size=1024**2):
                    temporary.write(chunk)
                    digest.update(chunk); part_hash.update(chunk)
                    total += len(chunk); part_size += len(chunk)
                    if total > settings.importacao_max_bytes or part_size > expected_size:
                        raise ValueError("Arquivo excede tamanho declarado.")
                    if time.monotonic() - last >= 2:
                        heartbeat(db, jid, token); last = time.monotonic()
            finally:
                body.close()
            if part_size != expected_size or part_hash.hexdigest() != expected:
                raise ValueError("Arquivo corrompido.")
        current = verificar(db, jid, token, lock=True)
        if total != current.tamanho_bytes or (current.checksum and current.checksum != digest.hexdigest()):
            raise ValueError("Arquivo alterado.")
        current.checksum = digest.hexdigest()
        db.commit()
        temporary.flush()
        yield temporary.name


def linhas(path, formato):
    from app.services.importacao_stream import iter_registros
    for number, record in enumerate(iter_registros(path, formato), 1):
        if number > settings.importacao_max_registros:
            raise ValueError("Quantidade excede o limite configurado.")
        yield number, record


def encerrar(db, jid, token, state):
    job = verificar(db, jid, token, lock=True)
    job.status, job.lease_token, job.lease_ate = state, None, None
    registrar(db, "IMPORTACAO_ASYNC_" + state, "importacao", jid, job.instrumento_id,
              detalhe={"status": state, "processados": job.processados}, operacao_id=jid)
    db.commit()


def analisar(db, job, token):
    jid, formato = job.id, job.formato
    columns, samples, count = [], {}, 0
    with fonte(db, job, token) as path:
        last = time.monotonic()
        for number, record in linhas(path, formato):
            count = number
            for key, value in record.items():
                if key not in samples:
                    columns.append(key); samples[key] = []
                    if len(columns) > 100:
                        raise ValueError("Quantidade de colunas excede 100.")
                if len(samples[key]) < 3:
                    if len(json.dumps(value, ensure_ascii=False)) > 1024:
                        value = json.dumps(value, ensure_ascii=False)[:1024]
                    samples[key].append(value)
            if number % settings.importacao_batch_size == 0 or time.monotonic() - last >= 2:
                heartbeat(db, jid, token, number); last = time.monotonic()
    if not count:
        raise ValueError("Arquivo sem registros.")
    current = verificar(db, jid, token, lock=True)
    instrument = service.instrumento(db, current.instrumento_id)
    current.total, current.fase_processados = count, count
    current.schema_version = instrument.schema_version
    current.analise = {"nome": instrument.nome, "schema_version": instrument.schema_version,
        "total": count, "campos": service.campos(db, current.instrumento_id),
        "colunas": [{"origem": key, "chave_sugerida": chave_sugerida(key),
                    "tipo_sugerido": sugerir_tipo(samples[key]), "amostras": samples[key]} for key in columns]}
    db.commit()
    encerrar(db, jid, token, "AGUARDANDO_MAPA")


def dados_validados(record, config, by_key, fields):
    data = {}
    for mapping in config.mapeamentos:
        key = mapping.destino or mapping.novo.chave
        try:
            data[key] = converter(record.get(mapping.origem), by_key[key]["tipo"])
        except (ValueError, TypeError, OverflowError, RecursionError):
            return None, {"campo": by_key[key]["nome"], "mensagem": "Valor incompativel com " + by_key[key]["tipo"] + "."}
    try:
        _validar(fields, data)
    except HTTPException:
        return None, {"campo": "", "mensagem": "Campo obrigatorio ausente ou valor invalido."}
    return data, None


def salvar_validacao(db, jid, token, number, records, errors, count):
    job = verificar(db, jid, token)
    root = service.prefixo(job) + "validacao/" + str(job.geracao) + f"/{number}-{token}"
    data = b"".join(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode() + b"\n" for row in records)
    key = root + ".jsonl"
    armazenamento.salvar_upload(key, data, "application/x-ndjson")
    error_key, error_checksum = None, None
    if errors:
        error_data = b"".join(json.dumps(error, ensure_ascii=False).encode() + b"\n" for error in errors)
        error_key, error_checksum = root + "-erros.jsonl", hashlib.sha256(error_data).hexdigest()
        armazenamento.salvar_upload(error_key, error_data, "application/x-ndjson")
    job = verificar(db, jid, token, lock=True)
    db.add(Parte(job_id=jid, categoria="DADOS", numero=number, object_key=key, tamanho_bytes=len(data),
                 checksum=hashlib.sha256(data).hexdigest(), quantidade=len(records), linhas=count,
                 erros_key=error_key, erros_checksum=error_checksum, aplicada=False))
    job.validos += len(records); job.invalidos += len(errors); job.fase_processados += count
    report = dict(job.relatorio)
    report["erros"] = (report.get("erros", []) + errors)[:100]
    report["previa"] = (report.get("previa", []) + records)[:5]
    report.update(total=job.total, validos=job.validos, invalidos=job.invalidos)
    job.relatorio = report
    db.commit()


def validar(db, job, token):
    jid, formato = job.id, job.formato
    config = ConfiguracaoImportacao.model_validate(job.configuracao)
    by_key = {f["chave"]: f for f in job.schema_json}
    fields = [SimpleNamespace(**field) for field in job.schema_json]
    checkpoint = job.fase_processados
    number = db.scalar(select(func.count()).select_from(Parte).where(Parte.job_id == jid, Parte.categoria == "DADOS")) + 1
    records, errors, count, budget, last = [], [], 0, 0, time.monotonic()
    with fonte(db, job, token) as path:
        for index, record in linhas(path, formato):
            if index <= checkpoint:
                if time.monotonic() - last >= 2:
                    heartbeat(db, jid, token); last = time.monotonic()
                continue
            data, error = dados_validados(record, config, by_key, fields)
            if error:
                errors.append({"linha": index, **error})
            else:
                records.append({"linha": index, "dados": data})
                budget += len(json.dumps(data, ensure_ascii=False).encode())
            count += 1
            if count >= settings.importacao_batch_size or budget >= settings.importacao_batch_bytes:
                salvar_validacao(db, jid, token, number, records, errors, count)
                records, errors, count, budget, number = [], [], 0, 0, number + 1
        if count:
            salvar_validacao(db, jid, token, number, records, errors, count)
    job = verificar(db, jid, token)
    if job.fase_processados != job.total:
        raise ValueError("Contagem de registros alterada.")
    state = "ERROS_VALIDACAO" if job.invalidos else "AGUARDANDO_CONFIRMACAO"
    db.commit()
    encerrar(db, jid, token, state)


def importar(db, job, token):
    from app.services.importacao_bulk import gravar_lote
    jid = job.id
    while True:
        current = verificar(db, jid, token)
        part = db.scalar(select(Parte).where(Parte.job_id == jid, Parte.categoria == "DADOS",
                         Parte.aplicada.is_(False)).order_by(Parte.numero).limit(1))
        if not part:
            break
        number = part.numero
        rows = [json.loads(line) for line in service.ler_parte(part).splitlines()]
        current = verificar(db, jid, token, lock=True)
        registrar(db, "IMPORTACAO_LOTE_INTENCAO", "importacao", jid, current.instrumento_id,
                  detalhe={"quantidade": len(rows), "etapa": "INTENCAO_PERSISTIDA"}, operacao_id=jid)
        db.commit()
        current = verificar(db, jid, token, lock=True)
        db.scalar(select(Instrumento).where(Instrumento.id == current.instrumento_id).with_for_update())
        # Recheck after waiting on the instrument lock.
        service.instrumento(db, current.instrumento_id)
        if db.get(Instrumento, current.instrumento_id).schema_version != current.schema_version:
            raise HTTPException(409, "Schema alterado.")
        gravar_lote(db, current, rows)
        part = db.get(Parte, (jid, "DADOS", number))
        part.aplicada = True
        current.processados += len(rows)
        current.fase_processados = current.processados
        db.commit()
    current = verificar(db, jid, token, lock=True)
    if current.processados != current.total:
        raise ValueError("Importacao incompleta.")
    # One durable indexing job instead of one Redis message per imported record.
    index = IndexacaoJob(id=uuid.uuid5(jid, "indexacao"), instrumento_id=current.instrumento_id,
        tipo="REINDEXACAO", status="PENDENTE", total_estimado=current.total, processados=0)
    if not db.get(IndexacaoJob, index.id):
        db.add(index)
    current.status, current.lease_token, current.lease_ate = "CONCLUIDA", None, None
    registrar(db, "CONCLUIR_IMPORTACAO_ASYNC", "importacao", jid, current.instrumento_id,
              detalhe={"processados": current.processados}, operacao_id=jid)
    iid = current.instrumento_id
    db.commit()
    enqueue_indexacao({"tipo": "reindexacao", "job_id": str(index.id), "instrumento_id": str(iid)})


def processar_pendente(db, job_id=None):
    now = datetime.now(UTC)
    query = select(Job).where(
        or_(Job.status == "PENDENTE", Job.status.in_(service.EXECUTANDO)),
        or_(Job.lease_ate.is_(None), Job.lease_ate <= now))
    if job_id:
        query = query.where(Job.id == job_id)
    job = db.scalar(query.order_by(Job.criado_em, Job.id).with_for_update(skip_locked=True).limit(1))
    if not job:
        return False
    jid, token = job.id, uuid.uuid4()
    job.status = job.phase
    job.lease_token, job.lease_ate = token, now + timedelta(seconds=settings.jobs_lease_segundos)
    phase = job.phase
    db.commit()
    try:
        job = verificar(db, jid, token)
        if phase == "IMPORTANDO":
            lock = int.from_bytes(hashlib.sha256(("importacao:" + str(job.instrumento_id)).encode()).digest()[:8], "big", signed=True)
            with db.get_bind().connect() as guard:
                if not guard.scalar(select(func.pg_try_advisory_lock(lock))):
                    job.status, job.lease_token, job.lease_ate = "PENDENTE", None, None
                    db.commit()
                    return False
                guard.commit()
                try:
                    importar(db, job, token)
                finally:
                    try:
                        guard.execute(select(func.pg_advisory_unlock(lock))); guard.commit()
                    except Exception:
                        guard.invalidate()
        elif phase == "ANALISANDO":
            analisar(db, job, token)
        elif phase == "VALIDANDO":
            validar(db, job, token)
    except Exception as exc:
        db.rollback()
        current = db.scalar(select(Job).where(Job.id == jid).with_for_update())
        if current.lease_token == token and current.status == current.phase:
            current.status = "EXPIRADA" if current.expira_em <= datetime.now(UTC) else "PAUSADA" if isinstance(exc, HTTPException) and exc.status_code in {403, 404, 409} else "FALHOU"
            current.erro = ("Dados ou permissoes alterados; confira o instrumento." if current.status == "PAUSADA"
                            else str(exc.detail)[:255] if isinstance(exc, HTTPException) and exc.status_code == 422
                            else "Arquivo invalido ou falha de processamento. Consulte o relatorio e tente novamente.")
            current.lease_token, current.lease_ate = None, None
            actor = db.get(Usuario, current.usuario_id)
            registrar(db, "FALHAR_IMPORTACAO_ASYNC", "importacao", jid, current.instrumento_id, usuario=actor,
                      detalhe={"status": current.status, "processados": current.processados}, operacao_id=jid)
            db.commit()
        logging.getLogger("thor.jobs").warning(json.dumps({"evento": "IMPORTACAO_ASYNC_INTERROMPIDA",
                                                           "job_id": str(jid), "erro_tipo": type(exc).__name__}))
    return True


def limpar_expirado(db):
    now = datetime.now(UTC)
    job = db.scalar(select(Job).where(Job.expira_em <= now, Job.limpo_em.is_(None),
        or_(Job.lease_ate.is_(None), Job.lease_ate <= now)).order_by(Job.expira_em)
        .with_for_update(skip_locked=True).limit(1))
    if not job:
        return False
    if job.status != "CONCLUIDA":
        job.status = "EXPIRADA"
    job.lease_token, job.lease_ate = None, None
    prefix = service.prefixo(job)
    # Keep the row locked to prevent two cleaners from racing on the same prefix.
    armazenamento.limpar_prefixo(prefix)
    job.limpo_em = now
    registrar(db, "EXPIRAR_ARQUIVOS_IMPORTACAO", "importacao", job.id, job.instrumento_id,
              detalhe={"status": job.status}, usuario=db.get(Usuario, job.usuario_id), operacao_id=job.id)
    db.commit()
    return True
