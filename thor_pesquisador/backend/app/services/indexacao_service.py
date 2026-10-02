from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException
from redis import Redis
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.mongo import registros_collection
from app.db.session import SessionLocal
from app.models.enums import StatusIndexacaoJob, StatusRegistro, TipoCampo, TipoIndexacaoJob
from app.models.instrumento import IndexacaoJob, Instrumento, InstrumentoCampo
from app.schemas.busca import BuscaAvancadaIn

TEXTUAL_TYPES = {TipoCampo.TEXTO_CURTO.value, TipoCampo.TEXTO_LONGO.value, TipoCampo.URL.value, TipoCampo.DATA.value, TipoCampo.LISTA_SIMPLES.value}


def indice_nome(instrumento_id: uuid.UUID | str) -> str:
    return f"instrumento_{str(instrumento_id).replace('-', '_')}"


def redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_indexacao(payload: dict[str, Any]) -> None:
    try:
        redis_client().rpush(settings.indexacao_queue_name, json.dumps(payload, default=str))
    except Exception:
        # Indexacao e eventual; o registro canonico no MongoDB nao pode falhar por indisponibilidade da fila.
        return


def enqueue_registro(instrumento_id: uuid.UUID | str, registro_id: str, acao: str = "upsert") -> None:
    enqueue_indexacao({"tipo": "registro", "instrumento_id": str(instrumento_id), "registro_id": registro_id, "acao": acao})


def criar_job_reindexacao(db: Session, instrumento_id: uuid.UUID) -> IndexacaoJob:
    if not db.get(Instrumento, instrumento_id):
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    total = registros_collection().count_documents({"instrumento_id": str(instrumento_id), "status": {"$ne": StatusRegistro.EXCLUIDO.value}})
    job = IndexacaoJob(
        id=uuid.uuid4(),
        instrumento_id=instrumento_id,
        tipo=TipoIndexacaoJob.REINDEXACAO.value,
        status=StatusIndexacaoJob.PENDENTE.value,
        total_estimado=total,
        processados=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    enqueue_indexacao({"tipo": "reindexacao", "job_id": str(job.id), "instrumento_id": str(instrumento_id)})
    return job


def jobs_recentes(db: Session, limit: int = 5) -> list[IndexacaoJob]:
    return list(db.scalars(select(IndexacaoJob).order_by(desc(IndexacaoJob.criado_em)).limit(limit)))


def contar_jobs_falhos(db: Session) -> int:
    return int(db.query(IndexacaoJob).filter(IndexacaoJob.status == StatusIndexacaoJob.FALHOU.value).count())


def documento_indexavel(campos: list[InstrumentoCampo], doc: dict[str, Any]) -> dict[str, Any]:
    dados = doc.get("dados", {})
    titulo = _titulo(campos, dados)
    texto_geral = _texto_geral(campos, dados)
    return {
        "id": doc["_id"],
        "instrumento_id": doc["instrumento_id"],
        "schema_version": doc.get("schema_version", 1),
        "titulo": titulo,
        "texto_geral": texto_geral,
        "dados": dados,
        "status": doc.get("status", StatusRegistro.ATIVO.value),
        "possui_imagens": False,
        "criado_em": _iso(doc.get("criado_em")),
        "atualizado_em": _iso(doc.get("atualizado_em")),
    }


def buscar_avancado(db: Session, instrumento_id: uuid.UUID, payload: BuscaAvancadaIn) -> dict[str, Any]:
    campos = _campos(db, instrumento_id)
    filtro = _build_filter(campos, payload.filters)
    sort = _build_sort(campos, payload.sort)
    search_payload: dict[str, Any] = {
        "q": payload.q or "",
        "limit": payload.limit,
        "offset": payload.offset,
        "attributesToHighlight": ["titulo", "texto_geral"],
    }
    if filtro:
        search_payload["filter"] = filtro
    if sort:
        search_payload["sort"] = sort
    try:
        response = _meili_request("POST", f"/indexes/{indice_nome(instrumento_id)}/search", json=search_payload)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        return {
            "items": [],
            "total": 0,
            "limit": payload.limit,
            "offset": payload.offset,
            "indice_atualizado_em": None,
            "indice_defasado": True,
        }
    hits = response.get("hits", [])
    latest = _ultimo_job_concluido(db, instrumento_id)
    return {
        "items": hits,
        "total": int(response.get("estimatedTotalHits") or response.get("totalHits") or len(hits)),
        "limit": payload.limit,
        "offset": payload.offset,
        "indice_atualizado_em": latest.atualizado_em if latest else None,
        "indice_defasado": latest is None,
    }


def facetas(db: Session, instrumento_id: uuid.UUID) -> dict[str, Any]:
    campos = [campo for campo in _campos(db, instrumento_id) if campo.facetavel]
    if not campos:
        return {"instrumento_id": instrumento_id, "facetas": {}}
    try:
        response = _meili_request(
            "POST",
            f"/indexes/{indice_nome(instrumento_id)}/search",
            json={"q": "", "limit": 0, "facets": [f"dados.{campo.chave}" for campo in campos]},
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 404:
            raise
        return {"instrumento_id": instrumento_id, "facetas": {}}
    distribution = response.get("facetDistribution", {})
    return {"instrumento_id": instrumento_id, "facetas": distribution}


def processar_mensagem(raw: str) -> None:
    payload = json.loads(raw)
    if payload.get("tipo") == "registro":
        with SessionLocal() as db:
            try:
                _indexar_registro(db, uuid.UUID(payload["instrumento_id"]), payload["registro_id"], payload.get("acao", "upsert"))
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise
    elif payload.get("tipo") == "reindexacao":
        with SessionLocal() as db:
            _reindexar(db, uuid.UUID(payload["job_id"]), uuid.UUID(payload["instrumento_id"]))
    elif payload.get("tipo") == "schema":
        with SessionLocal() as db:
            instrumento_id = uuid.UUID(payload["instrumento_id"])
            try:
                _configurar_indice(instrumento_id, _campos(db, instrumento_id))
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise


def run_worker_once(timeout: int = 5) -> bool:
    item = redis_client().blpop(settings.indexacao_queue_name, timeout=timeout)
    if not item:
        return False
    _queue, raw = item
    processar_mensagem(raw)
    return True


def _indexar_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, acao: str) -> None:
    if acao == "delete":
        _meili_request("DELETE", f"/indexes/{indice_nome(instrumento_id)}/documents/{registro_id}", allow_not_found=True)
        return
    doc = registros_collection().find_one({"_id": registro_id, "instrumento_id": str(instrumento_id)})
    if not doc or doc.get("status") == StatusRegistro.EXCLUIDO.value:
        _meili_request("DELETE", f"/indexes/{indice_nome(instrumento_id)}/documents/{registro_id}", allow_not_found=True)
        return
    campos = _campos(db, instrumento_id)
    _configurar_indice(instrumento_id, campos)
    _meili_request("POST", f"/indexes/{indice_nome(instrumento_id)}/documents", json=[documento_indexavel(campos, doc)])


def _reindexar(db: Session, job_id: uuid.UUID, instrumento_id: uuid.UUID) -> None:
    job = db.get(IndexacaoJob, job_id)
    if not job:
        return
    try:
        job.status = StatusIndexacaoJob.PROCESSANDO.value
        job.erro = None
        db.commit()
        campos = _campos(db, instrumento_id)
        _configurar_indice(instrumento_id, campos)
        collection = registros_collection()
        filtro: dict[str, Any] = {"instrumento_id": str(instrumento_id), "status": {"$ne": StatusRegistro.EXCLUIDO.value}}
        batch: list[dict[str, Any]] = []
        processados = 0
        for doc in collection.find(filtro).sort([("_id", 1)]):
            batch.append(documento_indexavel(campos, doc))
            if len(batch) >= settings.indexacao_batch_size:
                _meili_request("POST", f"/indexes/{indice_nome(instrumento_id)}/documents", json=batch)
                processados += len(batch)
                job.processados = processados
                job.ultimo_cursor_mongodb = batch[-1]["id"]
                job.atualizado_em = datetime.now(UTC)
                db.commit()
                batch = []
        if batch:
            _meili_request("POST", f"/indexes/{indice_nome(instrumento_id)}/documents", json=batch)
            processados += len(batch)
            job.processados = processados
            job.ultimo_cursor_mongodb = batch[-1]["id"]
        job.status = StatusIndexacaoJob.CONCLUIDO.value
        job.atualizado_em = datetime.now(UTC)
        db.commit()
    except Exception as exc:
        db.rollback()
        job = db.get(IndexacaoJob, job_id)
        if job:
            job.status = StatusIndexacaoJob.FALHOU.value
            job.erro = str(exc)
            job.atualizado_em = datetime.now(UTC)
            db.commit()


def _configurar_indice(instrumento_id: uuid.UUID, campos: list[InstrumentoCampo]) -> None:
    uid = indice_nome(instrumento_id)
    _meili_request("POST", "/indexes", json={"uid": uid, "primaryKey": "id"}, allow_conflict=True)
    filterable = ["status", "instrumento_id"] + [f"dados.{campo.chave}" for campo in campos if campo.filtro_avancado or campo.facetavel]
    sortable = ["criado_em", "atualizado_em"] + [f"dados.{campo.chave}" for campo in campos if campo.ordenavel]
    _meili_request("PUT", f"/indexes/{uid}/settings/filterable-attributes", json=filterable)
    _meili_request("PUT", f"/indexes/{uid}/settings/sortable-attributes", json=sortable)


def _campos(db: Session, instrumento_id: uuid.UUID) -> list[InstrumentoCampo]:
    if not db.get(Instrumento, instrumento_id):
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    return list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == instrumento_id).order_by(InstrumentoCampo.ordem.asc())))


def _build_filter(campos: list[InstrumentoCampo], filters: dict[str, Any]) -> list[str]:
    allowed = {campo.chave: campo for campo in campos if campo.filtro_avancado}
    clauses: list[str] = ['status != "EXCLUIDO"']
    for key, value in filters.items():
        campo = allowed.get(key)
        if not campo or value in (None, "", []):
            continue
        attr = f"dados.{key}"
        if isinstance(value, dict):
            if value.get("gte") not in (None, ""):
                clauses.append(f"{attr} >= {_quote(value['gte'])}")
            if value.get("lte") not in (None, ""):
                clauses.append(f"{attr} <= {_quote(value['lte'])}")
        elif campo.tipo == TipoCampo.LISTA_MULTIPLA.value and isinstance(value, list):
            clauses.append("(" + " OR ".join(f"{attr} = {_quote(item)}" for item in value) + ")")
        else:
            clauses.append(f"{attr} = {_quote(value)}")
    return clauses


def _build_sort(campos: list[InstrumentoCampo], sort: list[str]) -> list[str]:
    allowed = {campo.chave for campo in campos if campo.ordenavel}
    result: list[str] = []
    for item in sort:
        key, _, direction = item.partition(":")
        direction = direction or "asc"
        if key in allowed and direction in {"asc", "desc"}:
            result.append(f"dados.{key}:{direction}")
        elif key in {"criado_em", "atualizado_em"} and direction in {"asc", "desc"}:
            result.append(f"{key}:{direction}")
    return result


def _titulo(campos: list[InstrumentoCampo], dados: dict[str, Any]) -> str:
    preferred = ["titulo", "nome", "assunto", "descricao"]
    for key in preferred:
        value = dados.get(key)
        if value:
            return str(value)
    for campo in campos:
        value = dados.get(campo.chave)
        if value and campo.tipo in TEXTUAL_TYPES:
            return str(value)
    return "Registro sem titulo"


def _texto_geral(campos: list[InstrumentoCampo], dados: dict[str, Any]) -> str:
    keys = {campo.chave for campo in campos if campo.aparece_busca}
    return " ".join(_value_text(dados[key]) for key in keys if key in dados)


def _value_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(_value_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_value_text(item) for item in value.values())
    return str(value)


def _quote(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    escaped = str(value).replace('"', '\\"')
    return f'"{escaped}"'


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None:
        return datetime.now(UTC).isoformat()
    return str(value)


def _ultimo_job_concluido(db: Session, instrumento_id: uuid.UUID) -> IndexacaoJob | None:
    return db.scalar(
        select(IndexacaoJob)
        .where(IndexacaoJob.instrumento_id == instrumento_id, IndexacaoJob.status == StatusIndexacaoJob.CONCLUIDO.value)
        .order_by(desc(IndexacaoJob.atualizado_em))
        .limit(1)
    )


def _meili_request(method: str, path: str, json: Any | None = None, allow_conflict: bool = False, allow_not_found: bool = False) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {settings.meilisearch_api_key}"}
    url = f"{settings.meilisearch_url.rstrip('/')}{path}"
    with httpx.Client(timeout=15) as client:
        response = client.request(method, url, json=json, headers=headers)
    if allow_conflict and response.status_code == 409:
        return {}
    if allow_not_found and response.status_code == 404:
        return {}
    response.raise_for_status()
    if not response.content:
        return {}
    return response.json()
