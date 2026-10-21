"""Batch persistence under the caller's instrument/job locks and lease fence."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from pymongo import UpdateOne, timeout
from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.observability import request_id_context
from app.db.mongo import registros_collection
from app.models.conformidade import AuditoriaGeral
from app.models.editorial import EditorialRegistro
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.services import registro_service


def gravar_lote(db: Session, job, registros: list[dict]) -> int:
    """Persist a canonical batch already validated and bounded to 8 MiB by the caller.

    The caller holds instrument/job row locks and its lease fence through commit,
    atomically committing SQL effects together with the batch checkpoint.
    """
    if not registros:
        return 0
    if len(registros) > 1000:
        raise HTTPException(422, "Lote excede o limite de 1000 registros.")
    linhas = [r["linha"] for r in registros]
    if any(type(linha) is not int or linha < 1 for linha in linhas) or len(set(linhas)) != len(linhas):
        raise HTTPException(422, "Linhas do lote devem ser positivas e unicas.")

    actor = db.info["usuario"]
    campos = list(db.scalars(select(InstrumentoCampo).where(
        InstrumentoCampo.instrumento_id == job.instrumento_id).order_by(InstrumentoCampo.ordem)))
    now = datetime.now(UTC)
    documentos = {}
    for registro in registros:
        dados, linha = registro["dados"], registro["linha"]
        registro_service._validar(campos, dados)
        rid = str(uuid.uuid5(job.id, str(linha - 1)))
        documentos[rid] = {
            "_id": rid, "_importacao_id": str(job.id), "_importacao_linha": linha,
            "_revision": 1, "instrumento_id": str(job.instrumento_id),
            "schema_version": job.schema_version, "dados": dados, "status": "ATIVO",
            "criado_por": str(actor.id), "atualizado_por": str(actor.id),
            "criado_em": now, "atualizado_em": now,
            "texto_busca_basico": registro_service._texto_busca(campos, dados),
        }

    ids = list(documentos)
    collection = registros_collection()
    with timeout(30):
        existentes = {doc["_id"]: doc for doc in collection.find(
            {"_id": {"$in": ids}},
            {"_id": 1, "instrumento_id": 1, "_importacao_id": 1,
             "_importacao_linha": 1, "_revision": 1, "status": 1})}
    controle = EditorialRegistro.__table__
    controles = set(db.scalars(select(controle.c.registro_id).where(
        controle.c.instrumento_id == job.instrumento_id, controle.c.registro_id.in_(ids))))
    # Check the whole batch before writing: a tombstone must never be resurrected.
    for rid, documento in documentos.items():
        existente = existentes.get(rid)
        if existente is not None:
            if (existente.get("_importacao_id") != str(job.id)
                    or existente.get("_importacao_linha") != documento["_importacao_linha"]
                    or existente.get("instrumento_id") != str(job.instrumento_id)):
                raise HTTPException(409, "Identificador de registro pertence a outra origem.")
        elif rid in controles:
            raise HTTPException(409, "Registro removido ou em reconciliacao; nao sera recriado pela importacao.")

    auditoria = AuditoriaGeral.__table__
    auditados = set(db.scalars(select(auditoria.c.registro_id).where(
        auditoria.c.operacao_id == job.id, auditoria.c.instrumento_id == job.instrumento_id,
        auditoria.c.acao == "CRIAR_REGISTRO_CONCLUIDO", auditoria.c.registro_id.in_(ids))))
    with timeout(30):
        collection.bulk_write([UpdateOne(
            {"_id": rid, "instrumento_id": doc["instrumento_id"],
             "_importacao_id": doc["_importacao_id"], "_importacao_linha": doc["_importacao_linha"]},
            {"$setOnInsert": doc}, upsert=True) for rid, doc in documentos.items()], ordered=False)

    novos_controles = []
    for rid, documento in documentos.items():
        if rid not in controles:
            origem = existentes.get(rid, documento)
            novos_controles.append({
                "instrumento_id": job.instrumento_id, "registro_id": rid,
                "status_editorial": "RASCUNHO",
                "status_operacional": origem.get("status", "ATIVO"),
                "versao": origem.get("_revision", 1),
            })
    if novos_controles:
        db.execute(pg_insert(controle).values(novos_controles).on_conflict_do_nothing(
            constraint="uq_editorial_registro"))

    # An API edit may have created a control for a Mongo orphan before this retry.
    eventos = [{
        "usuario_id": actor.id, "agente": actor.nome,
        "acao": "CRIAR_REGISTRO_CONCLUIDO", "entidade": "registro",
        "entidade_id": rid, "instrumento_id": job.instrumento_id, "registro_id": rid,
        "request_id": request_id_context.get(), "operacao_id": job.id,
        "detalhe": {"etapa": "CONCLUIDA"},
    } for rid in ids if rid not in auditados]
    if eventos:
        db.execute(insert(auditoria).values(eventos))
    db.execute(update(Instrumento.__table__).where(Instrumento.id == job.instrumento_id)
               .values(revisao_dados=Instrumento.revisao_dados + 1))
    return len(registros)
