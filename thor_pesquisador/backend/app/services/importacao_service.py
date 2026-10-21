"""Validated, resumable creation using the existing schema, record and audit services."""
import hashlib
import json
import uuid
from types import SimpleNamespace
from fastapi import HTTPException
from sqlalchemy import func, select
from app.db.mongo import registros_collection
from app.models.importacao import ImportacaoRegistros
from app.models.editorial import EditorialRegistro
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.schemas.registro import RegistroCreate
from app.schemas.instrumento_campo import InstrumentoCampoCreate, InstrumentoCampoOut
from app.services import registro_service
from app.services.auditoria_service import registrar
from app.services.editorial_service import controle
from app.services.instrumento_service import _editar_schema
from app.services.indexacao_service import enqueue_indexacao
from app.services.permissao_service import require
from app.services.importacao_arquivo import ler_arquivo, converter, sugerir_tipo, chave_sugerida


def instrumento(db, iid):
    require(db, "registros_incluir", iid)
    require(db, "instrumentos_consultar", iid)
    row = db.scalar(select(Instrumento).where(Instrumento.id == iid).execution_options(populate_existing=True))
    if not row:
        raise HTTPException(404, "Instrumento nao encontrado.")
    if row.status == "ARQUIVADO":
        raise HTTPException(409, "Reabra o instrumento antes de importar.")
    return row


def analisar(db, iid, content, filename):
    row = instrumento(db, iid)
    columns, records, info = ler_arquivo(content, filename)
    fields = list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == iid)
                             .order_by(InstrumentoCampo.ordem, InstrumentoCampo.id)))
    return {**info, "nome": row.nome, "schema_version": row.schema_version, "total": len(records),
            "colunas": [{"origem": key, "chave_sugerida": chave_sugerida(key),
                        "tipo_sugerido": sugerir_tipo([r.get(key) for r in records]),
                        "amostras": [r.get(key) for r in records[:3]]} for key in columns],
            "campos": [InstrumentoCampoOut.model_validate(f).model_dump(mode="json") for f in fields]}


def assinatura(content, config):
    return hashlib.sha256(content + json.dumps(config.model_dump(mode="json"), sort_keys=True,
                                               separators=(",", ":")).encode()).hexdigest()


def existente(db, iid, config, content):
    job = db.get(ImportacaoRegistros, config.operacao_id)
    if job and (job.instrumento_id != iid or job.usuario_id != db.info["usuario"].id
                or job.assinatura != assinatura(content, config)):
        raise HTTPException(409, "Operacao ja utilizada com outro arquivo, usuario ou mapeamento.")
    return job


def preparar(db, iid, content, filename, config):
    row = instrumento(db, iid)
    columns, records, _ = ler_arquivo(content, filename)
    job = existente(db, iid, config, content)
    expected = job.schema_version if job else config.schema_version
    if row.schema_version != expected:
        raise HTTPException(409, "Schema alterado. Analise novamente o arquivo e o mapeamento.")
    fields = list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == iid)))
    by_key = {f.chave: f for f in fields}
    used_sources, used_targets, new_fields = set(), set(), []
    mappings = []
    for mapping in config.mapeamentos:
        if mapping.origem not in columns or mapping.origem in used_sources:
            raise HTTPException(422, "Coluna de origem inexistente ou mapeada mais de uma vez.")
        used_sources.add(mapping.origem)
        key = mapping.destino or mapping.novo.chave
        if key in used_targets:
            raise HTTPException(422, "Mais de uma coluna foi associada ao mesmo campo.")
        used_targets.add(key)
        if mapping.novo:
            require(db, "campos_incluir", iid)
            if key in by_key and not job:
                raise HTTPException(409, "Chave de novo campo ja existe: " + key)
            if not job:
                payload = InstrumentoCampoCreate(**mapping.novo.model_dump())
                field = SimpleNamespace(**payload.model_dump(mode="json"))
                by_key[key] = field
                fields.append(field)
                new_fields.append(payload)
            elif key not in by_key:
                raise HTTPException(409, "Campo criado pela importacao foi removido.")
        if key not in by_key:
            raise HTTPException(422, "Campo de destino nao existe no instrumento.")
        mappings.append((mapping.origem, by_key[key]))
    converted, errors, invalid = [], [], 0
    for index, record in enumerate(records, 1):
        data, row_errors = {}, []
        for source, field in mappings:
            try:
                data[field.chave] = converter(record.get(source), field.tipo)
            except (ValueError, TypeError, OverflowError, RecursionError):
                row_errors.append({"linha": index, "campo": field.nome, "mensagem": "Valor incompativel com " + field.tipo + "."})
        if not row_errors:
            try:
                registro_service._validar(fields, data)
            except HTTPException as exc:
                row_errors.append({"linha": index, "campo": "", "mensagem": exc.detail})
        if row_errors:
            invalid += 1
            errors.extend(row_errors[:max(0, 100 - len(errors))])
        converted.append(data)
    report = {"total": len(records), "validos": len(records) - invalid, "invalidos": invalid,
              "erros": errors, "previa": [{"linha": i + 1, "dados": data} for i, data in enumerate(converted[:5])],
              "novos_campos": [p.model_dump(mode="json") for p in new_fields]}
    return row, job, new_fields, converted, report


def validar(db, iid, content, filename, config):
    return preparar(db, iid, content, filename, config)[-1]


def serializar(job):
    return {"id": str(job.id), "status": job.status, "total": job.total, "processados": job.processados,
            "configuracao": job.configuracao, "criado_em": job.criado_em, "atualizado_em": job.atualizado_em}


def listar(db, iid):
    instrumento(db, iid)
    rows = db.scalars(select(ImportacaoRegistros).where(ImportacaoRegistros.instrumento_id == iid,
        ImportacaoRegistros.usuario_id == db.info["usuario"].id).order_by(ImportacaoRegistros.criado_em.desc()).limit(20))
    return [serializar(job) for job in rows]


def executar(db, iid, content, filename, config):
    instrumento(db, iid)
    # Services commit per operation. A separate connection keeps the session lock across those commits.
    lock = int.from_bytes(hashlib.sha256(("importacao:" + str(iid)).encode()).digest()[:8], "big", signed=True)
    with db.get_bind().connect() as guard:
        if not guard.scalar(select(func.pg_try_advisory_lock(lock))):
            raise HTTPException(409, "Outra importacao deste instrumento esta em andamento.")
        guard.commit()
        try:
            return _executar(db, iid, content, filename, config)
        finally:
            try:
                guard.execute(select(func.pg_advisory_unlock(lock)))
                guard.commit()
            except Exception:
                guard.invalidate()


def _executar(db, iid, content, filename, config):
    job = existente(db, iid, config, content)
    if job and job.status == "CONCLUIDA":
        return serializar(job)
    # Schema validation and its mutation share the instrument row lock.
    db.scalar(select(Instrumento).where(Instrumento.id == iid).with_for_update())
    row, job, new_fields, records, report = preparar(db, iid, content, filename, config)
    if report["invalidos"]:
        raise HTTPException(422, {"mensagem": "Corrija os erros antes de importar. Nenhum registro foi criado.", **report})
    if not job:
        if new_fields:
            _editar_schema(db, iid, "campos_incluir")
            order = db.scalar(select(func.max(InstrumentoCampo.ordem)).where(InstrumentoCampo.instrumento_id == iid)) or 0
            for index, payload in enumerate(new_fields, 1):
                db.add(InstrumentoCampo(instrumento_id=iid, **payload.model_dump(mode="json", exclude={"ordem"}), ordem=order + index))
        job = ImportacaoRegistros(id=config.operacao_id, instrumento_id=iid, usuario_id=db.info["usuario"].id,
            assinatura=assinatura(content, config), configuracao=config.model_dump(mode="json"),
            schema_version=row.schema_version, total=len(records), processados=0, status="EM_ANDAMENTO")
        db.add(job)
        registrar(db, "INICIAR_IMPORTACAO", "importacao", job.id, iid,
                  detalhe={"quantidade": len(records), "status": job.status}, operacao_id=job.id)
        db.commit()
    try:
        if any(mapping.novo for mapping in config.mapeamentos):
            enqueue_indexacao({"tipo": "schema", "instrumento_id": str(iid)})
        job.status = "EM_ANDAMENTO"
        db.commit()
        for index, data in enumerate(records):
            if index < job.processados:
                continue
            actor = db.info["usuario"]
            db.refresh(actor)
            if not actor.ativo or actor.excluido_em is not None:
                raise HTTPException(403, "Usuario inativo.")
            current = instrumento(db, iid)
            if current.schema_version != job.schema_version:
                raise HTTPException(409, "Schema alterado durante a importacao.")
            rid = str(uuid.uuid5(job.id, str(index)))
            doc = registros_collection().find_one({"_id": rid, "instrumento_id": str(iid)})
            if doc:
                # Recover the SQL side after an acknowledged Mongo insert; never overwrite later user edits.
                controle(db, iid, rid, doc)
                registrar(db, "RETOMAR_REGISTRO_IMPORTACAO", "registro", rid, iid, rid,
                          detalhe={"etapa": "CONCLUIDA"}, operacao_id=job.id)
                db.commit()
                registro_service.enqueue_registro(iid, rid)
            else:
                if db.scalar(select(EditorialRegistro.id).where(EditorialRegistro.instrumento_id == iid,
                                                                 EditorialRegistro.registro_id == rid)):
                    raise HTTPException(409, "Registro removido ou em reconciliacao; nao sera recriado pela importacao.")
                registro_service.criar_registro(db, iid, RegistroCreate(dados=data), actor.id, registro_id=rid)
            job.processados = index + 1
            db.commit()
        job.status = "CONCLUIDA"
        registrar(db, "CONCLUIR_IMPORTACAO", "importacao", job.id, iid,
                  detalhe={"processados": job.processados, "status": job.status}, operacao_id=job.id)
        db.commit()
    except Exception:
        db.rollback()
        job = db.get(ImportacaoRegistros, config.operacao_id)
        job.status = "INTERROMPIDA"
        registrar(db, "INTERROMPER_IMPORTACAO", "importacao", job.id, iid,
                  detalhe={"processados": job.processados, "status": job.status}, operacao_id=job.id)
        db.commit()
    return serializar(job)
