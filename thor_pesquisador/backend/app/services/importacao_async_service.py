"""Durable asynchronous import commands; request handlers never parse the full source."""
import csv
import hashlib
import io
import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import PurePosixPath
from types import SimpleNamespace
from fastapi import HTTPException
from sqlalchemy import delete, func, or_, select
from app.core.config import settings
from app.models.importacao_async import ImportacaoAsync as Job, ImportacaoAsyncParte as Parte
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.models.user import Usuario
from app.schemas.importacao import ConfiguracaoImportacao
from app.schemas.instrumento_campo import InstrumentoCampoCreate, InstrumentoCampoOut
from app.services.armazenamento_service import armazenamento
from app.services.auditoria_service import registrar
from app.services.instrumento_service import _editar_schema
from app.services.permissao_service import require

ATIVOS = {"RECEBENDO", "ANALISANDO", "VALIDANDO", "PENDENTE", "IMPORTANDO"}
EXECUTANDO = {"ANALISANDO", "VALIDANDO", "IMPORTANDO"}


def limites():
    return {"max_bytes": settings.importacao_max_bytes, "max_registros": settings.importacao_max_registros,
            "chunk_bytes": settings.importacao_chunk_bytes}


def instrumento(db, iid):
    actor = require(db, "registros_incluir", iid)
    require(db, "instrumentos_consultar", iid)
    if not actor.ativo or actor.excluido_em is not None:
        raise HTTPException(403, "Usuario inativo.")
    row = db.scalar(select(Instrumento).where(Instrumento.id == iid).execution_options(populate_existing=True))
    if not row:
        raise HTTPException(404, "Instrumento nao encontrado.")
    if row.status == "ARQUIVADO":
        raise HTTPException(409, "Instrumento arquivado.")
    return row


def obter(db, iid, jid, lock=False, exigir_arquivo=True):
    instrumento(db, iid)
    query = select(Job).where(Job.id == jid, Job.instrumento_id == iid, Job.usuario_id == db.info["usuario"].id)
    job = db.scalar(query.with_for_update() if lock else query)
    if not job:
        raise HTTPException(404, "Importacao nao encontrada.")
    if exigir_arquivo and (job.expira_em <= datetime.now(UTC) or job.limpo_em):
        raise HTTPException(410, "Arquivos da importacao expiraram.")
    return job


def saida(job):
    elapsed = max(1, (datetime.now(UTC) - (job.inicio_fase or job.criado_em)).total_seconds())
    receiving = job.status == "RECEBENDO"
    count = job.bytes_recebidos if receiving else job.processados if job.phase == "IMPORTANDO" else job.fase_processados
    total = job.tamanho_bytes if receiving else job.total
    rate = round(count / elapsed, 2) if job.status in EXECUTANDO or receiving else 0
    remaining = max(0, total - count)
    return {key: getattr(job, key) for key in (
        "id", "status", "phase", "nome_arquivo", "tamanho_bytes", "bytes_recebidos", "total", "processados",
        "fase_processados", "validos", "invalidos", "erro", "analise", "configuracao", "relatorio",
        "criado_em", "atualizado_em", "expira_em")} | {
        "analise": job.analise or None, "configuracao": job.configuracao or None,
        "relatorio": job.relatorio or None,
        "velocidade": rate, "estimativa_segundos": round(remaining / rate) if rate and total else None}


def prefixo(job):
    return "importacoes-assincronas/" + str(job.id) + "/"


def listar(db, iid, limit, offset, q="", status=""):
    instrumento(db, iid)
    query = select(Job).where(Job.instrumento_id == iid, Job.usuario_id == db.info["usuario"].id)
    if q.strip():
        query = query.where(Job.nome_arquivo.ilike("%" + q.strip()[:150] + "%"))
    if status:
        query = query.where(Job.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    jobs = db.scalars(query.order_by(Job.criado_em.desc(), Job.id).limit(limit).offset(offset))
    return {"items": [saida(j) for j in jobs], "total": total, "limit": limit, "offset": offset}


def criar(db, iid, operation, filename, size):
    row = instrumento(db, iid)
    filename = PurePosixPath(filename.replace("\\", "/")).name
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in {"csv", "json", "jsonl", "ndjson"} or not filename.strip() or "\x00" in filename:
        raise HTTPException(422, "Selecione CSV, JSON ou JSONL.")
    if not 0 < size <= settings.importacao_max_bytes:
        raise HTTPException(413, "Arquivo excede o limite configurado.")
    actor = db.info["usuario"]
    db.execute(select(func.pg_advisory_xact_lock(int(actor.id.int % (2**63 - 1)))))
    existing = db.get(Job, operation)
    if existing:
        if (existing.usuario_id, existing.instrumento_id, existing.nome_arquivo, existing.tamanho_bytes) != (actor.id, iid, filename, size):
            raise HTTPException(409, "Identificador de operacao ja utilizado.")
        return saida(existing)
    active = db.scalar(select(func.count()).select_from(Job).where(Job.usuario_id == actor.id,
        Job.status.not_in({"CONCLUIDA", "CANCELADA", "EXPIRADA"}), Job.expira_em > datetime.now(UTC)))
    if active >= 5:
        raise HTTPException(409, "Limite de cinco importacoes ativas por usuario.")
    job = Job(id=operation, usuario_id=actor.id, instrumento_id=iid, nome_arquivo=filename, formato=extension,
        tamanho_bytes=size, schema_version=row.schema_version,
        expira_em=datetime.now(UTC) + timedelta(days=settings.importacao_retencao_dias))
    db.add(job)
    registrar(db, "SOLICITAR_IMPORTACAO_ASYNC", "importacao", job.id, iid,
              detalhe={"status": "RECEBENDO"}, operacao_id=job.id)
    db.commit()
    return saida(job)


def parte(db, iid, jid, number, data):
    job = obter(db, iid, jid, lock=True)
    if job.status != "RECEBENDO" or number < 1:
        raise HTTPException(409, "Importacao nao esta recebendo arquivo.")
    chunk = settings.importacao_chunk_bytes
    expected = min(chunk, job.tamanho_bytes - (number - 1) * chunk)
    if expected <= 0 or len(data) != expected:
        raise HTTPException(422, "Tamanho ou numero da parte invalido.")
    digest = hashlib.sha256(data).hexdigest()
    saved = db.get(Parte, (jid, "FONTE", number))
    if saved:
        if saved.checksum != digest:
            raise HTTPException(409, "Parte ja recebida com outro conteudo.")
        return saida(job)
    if (number - 1) * chunk != job.bytes_recebidos:
        raise HTTPException(409, "Envie as partes em ordem ou consulte o progresso.")
    key = prefixo(job) + f"fonte/{number}-{digest}"
    armazenamento.salvar_upload(key, data, "application/octet-stream")
    db.add(Parte(job_id=jid, categoria="FONTE", numero=number, object_key=key, checksum=digest,
                 tamanho_bytes=len(data), quantidade=0, linhas=0, aplicada=False))
    job.bytes_recebidos += len(data)
    db.commit()
    return saida(job)


def iniciar_fase(job, phase):
    job.phase = phase
    job.status = phase
    job.erro = None
    job.lease_token, job.lease_ate = None, None
    job.inicio_fase = datetime.now(UTC)


def finalizar(db, iid, jid):
    job = obter(db, iid, jid, lock=True)
    if job.status != "RECEBENDO":
        return saida(job)
    if job.bytes_recebidos != job.tamanho_bytes:
        raise HTTPException(409, "Upload incompleto.")
    iniciar_fase(job, "ANALISANDO")
    registrar(db, "ENFILEIRAR_ANALISE_IMPORTACAO", "importacao", jid, iid, operacao_id=jid)
    db.commit()
    return saida(job)


def campos(db, iid):
    return [InstrumentoCampoOut.model_validate(field).model_dump(mode="json") for field in db.scalars(
        select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == iid).order_by(InstrumentoCampo.ordem, InstrumentoCampo.id))]


def plano(db, job, config):
    row = instrumento(db, job.instrumento_id)
    if config.operacao_id != job.id or config.schema_version != row.schema_version:
        raise HTTPException(409, "Schema ou operacao alterados. Reanalise o arquivo.")
    existing = campos(db, job.instrumento_id)
    by_key = {f["chave"]: f for f in existing}
    origins = {c["origem"] for c in job.analise.get("colunas", [])}
    sources, targets, additions = set(), set(), []
    for mapping in config.mapeamentos:
        key = mapping.destino or mapping.novo.chave
        if mapping.origem not in origins or mapping.origem in sources or key in targets:
            raise HTTPException(422, "Origem inexistente ou associacoes duplicadas.")
        sources.add(mapping.origem); targets.add(key)
        if mapping.novo:
            require(db, "campos_incluir", job.instrumento_id)
            if key in by_key:
                raise HTTPException(409, "Chave de novo campo ja existe: " + key)
            new = InstrumentoCampoCreate(**mapping.novo.model_dump()).model_dump(mode="json")
            additions.append(new); by_key[key] = new
        if key not in by_key:
            raise HTTPException(422, "Campo de destino inexistente.")
    return list(by_key.values()), additions


def validar(db, iid, jid, config):
    job = obter(db, iid, jid, lock=True)
    if job.status not in {"AGUARDANDO_MAPA", "ERROS_VALIDACAO", "AGUARDANDO_CONFIRMACAO"} or job.processados:
        raise HTTPException(409, "Importacao nao permite alterar o mapeamento neste estado.")
    schema, _ = plano(db, job, config)
    job.configuracao, job.schema_json = config.model_dump(mode="json"), schema
    job.schema_version = config.schema_version
    job.geracao = uuid.uuid4()
    job.validos, job.invalidos, job.fase_processados = 0, 0, 0
    job.relatorio = {"erros": [], "previa": [], "total": job.total, "validos": 0, "invalidos": 0}
    db.execute(delete(Parte).where(Parte.job_id == jid, Parte.categoria == "DADOS"))
    iniciar_fase(job, "VALIDANDO")
    registrar(db, "VALIDAR_IMPORTACAO_ASYNC", "importacao", jid, iid, operacao_id=jid)
    db.commit()
    return saida(job)


def confirmar(db, iid, jid):
    job = obter(db, iid, jid, lock=True)
    if job.status in {"PENDENTE", "IMPORTANDO", "CONCLUIDA"}:
        return saida(job)
    if job.status != "AGUARDANDO_CONFIRMACAO" or job.invalidos:
        raise HTTPException(409, "Valide todos os registros antes de confirmar.")
    db.scalar(select(Instrumento).where(Instrumento.id == iid).with_for_update())
    config = ConfiguracaoImportacao.model_validate(job.configuracao)
    _, additions = plano(db, job, config)
    if additions:
        row = _editar_schema(db, iid, "campos_incluir")
        order = db.scalar(select(func.max(InstrumentoCampo.ordem)).where(InstrumentoCampo.instrumento_id == iid)) or 0
        for index, definition in enumerate(additions, 1):
            definition["ordem"] = order + index
            db.add(InstrumentoCampo(instrumento_id=iid, **definition))
        job.schema_version = row.schema_version
    iniciar_fase(job, "IMPORTANDO")
    job.status = "PENDENTE"
    registrar(db, "CONFIRMAR_IMPORTACAO_ASYNC", "importacao", jid, iid, detalhe={"quantidade": job.total}, operacao_id=jid)
    db.commit()
    return saida(job)


def cancelar(db, iid, jid):
    job = obter(db, iid, jid, lock=True)
    if job.status in {"CONCLUIDA", "EXPIRADA"}:
        raise HTTPException(409, "Importacao ja encerrada.")
    job.status = "CANCELADA"
    job.lease_token, job.lease_ate = None, None
    registrar(db, "CANCELAR_IMPORTACAO_ASYNC", "importacao", jid, iid,
              detalhe={"processados": job.processados}, operacao_id=jid)
    db.commit()
    return saida(job)


def retomar(db, iid, jid):
    job = obter(db, iid, jid, lock=True)
    if job.status not in {"PAUSADA", "FALHOU"}:
        raise HTTPException(409, "Somente falhas ou pausas podem ser retomadas.")
    row = instrumento(db, iid)
    if job.phase in {"VALIDANDO", "IMPORTANDO"} and row.schema_version != job.schema_version:
        raise HTTPException(409, "Schema alterado; reconciliacao necessaria antes de retomar.")
    iniciar_fase(job, job.phase)
    if job.phase == "IMPORTANDO":
        job.status = "PENDENTE"
    registrar(db, "RETOMAR_IMPORTACAO_ASYNC", "importacao", jid, iid, operacao_id=jid)
    db.commit()
    return saida(job)


def ler_parte(part):
    obj = armazenamento.obter_objeto(part.object_key)["Body"]
    try:
        data = obj.read(settings.importacao_batch_bytes + 2 * 1024**2 + 1)
    finally:
        obj.close()
    if len(data) != part.tamanho_bytes or hashlib.sha256(data).hexdigest() != part.checksum:
        raise RuntimeError("Checksum de lote invalido.")
    return data


def erros_csv(db, iid, jid):
    from app.services.exportacao_service import csv_value
    job = obter(db, iid, jid)
    if not job.invalidos:
        raise HTTPException(404, "Nenhum erro de validacao.")
    # Materialize only bounded descriptors, never the full report contents.
    parts = [(p.erros_key, p.erros_checksum) for p in db.scalars(select(Parte).where(
        Parte.job_id == jid, Parte.categoria == "DADOS", Parte.erros_key.is_not(None)).order_by(Parte.numero))]
    registrar(db, "BAIXAR_ERROS_IMPORTACAO", "importacao", jid, iid, operacao_id=jid)
    db.commit()
    def stream():
        yield b"\xef\xbb\xbfRegistro,Campo,Erro\r\n"
        for key, expected in parts:
            body = armazenamento.obter_objeto(key)["Body"]
            try:
                data = body.read(16 * 1024**2 + 1)
            finally:
                body.close()
            if len(data) > 16 * 1024**2 or hashlib.sha256(data).hexdigest() != expected:
                raise RuntimeError("Relatorio indisponivel.")
            output = io.StringIO(newline="")
            writer = csv.writer(output)
            for raw in data.splitlines():
                error = json.loads(raw)
                writer.writerow([error["linha"], csv_value(error["campo"]), csv_value(error["mensagem"])])
            yield output.getvalue().encode("utf-8")
    return stream()
