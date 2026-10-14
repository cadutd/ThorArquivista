"""Fail-closed public projections, isolated from the internal search index."""
import time
import logging
import json
import httpx
import uuid
from fastapi import HTTPException
from sqlalchemy import select, func
from app.db.mongo import snapshots_collection
from app.models.editorial import EditorialRegistro, PublicacaoInstrumento, PublicacaoImagem
from app.models.instrumento import Instrumento, InstrumentoCampo, IndexacaoJob
from app.services.indexacao_service import _meili_request


def indice(instrumento):
    return f"publico_{str(instrumento.id).replace('-', '_')}_{instrumento.geracao_publica}"


def publico(db, instrumento_id, lock=False):
    query = select(Instrumento).where(Instrumento.id == instrumento_id,
        Instrumento.visibilidade == "PUBLICO", Instrumento.publicacao_id.is_not(None),
        Instrumento.status != "ARQUIVADO")
    if lock:
        query = query.with_for_update(read=True)
    instrumento = db.scalar(query)
    if not instrumento or not db.get(PublicacaoInstrumento, instrumento.publicacao_id):
        raise HTTPException(404, "Instrumento nao encontrado.")
    return instrumento


def campos_publicos(db, schema):
    atuais = set(db.scalars(select(InstrumentoCampo.chave).where(
        InstrumentoCampo.instrumento_id == uuid.UUID(schema["id"]),
        InstrumentoCampo.exibir_publico.is_(True))))
    instrumento = db.get(Instrumento, uuid.UUID(schema["id"]))
    vigente = db.get(PublicacaoInstrumento, instrumento.publicacao_id) if instrumento.publicacao_id else None
    autorizados = {c["chave"] for c in vigente.schema_json["campos"] if c.get("exibir_publico")} if vigente else set()
    return [c for c in schema["campos"] if c.get("exibir_publico") and c["chave"] in atuais & autorizados]


def projecao(db, snapshot, campos=None):
    if campos is None:
        schema = db.get(PublicacaoInstrumento, uuid.UUID(snapshot["schema_id"]))
        if not schema:
            return None
        campos = campos_publicos(db, schema.schema_json)
    dados = {c["chave"]: snapshot["dados"][c["chave"]] for c in campos if c["chave"] in snapshot["dados"]}
    return {"id": snapshot["registro_id"], "instrumento_id": snapshot["instrumento_id"],
            "versao": snapshot["versao"], "dados": dados,
            "titulo": str(next(iter(dados.values()), "Registro")),
            "texto_geral": " ".join(str(v) for v in dados.values())}


def obter_registro(db, instrumento_id, registro_id):
    publico(db, instrumento_id, lock=True)
    row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == instrumento_id,
        EditorialRegistro.registro_id == registro_id, EditorialRegistro.status_operacional == "ATIVO",
        EditorialRegistro.status_editorial != "ARQUIVADO", EditorialRegistro.snapshot_id.is_not(None)))
    if not row:
        raise HTTPException(404, "Registro nao encontrado.")
    snapshot = snapshots_collection().find_one({"_id": row.snapshot_id}, {"imagens": 0})
    result = projecao(db, snapshot) if snapshot else None
    if not result:
        raise HTTPException(404, "Registro nao encontrado.")
    return result


def galeria(db, instrumento_id, registro_id, limit, offset):
    from app.models.imagem import ImagemDocumento
    obter_registro(db, instrumento_id, registro_id)
    row = db.scalar(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == instrumento_id,
        EditorialRegistro.registro_id == registro_id))
    query = select(PublicacaoImagem).join(ImagemDocumento).where(
        PublicacaoImagem.snapshot_id == row.snapshot_id, ImagemDocumento.direitos_acesso == "PUBLICO",
        PublicacaoImagem.referencia != {})
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    page = db.scalars(query.order_by(PublicacaoImagem.referencia["ordem"].as_integer(),
        PublicacaoImagem.imagem_id).limit(limit).offset(offset))
    return {"items": [v.referencia for v in page], "total": total, "limit": limit, "offset": offset}


def buscar(db, instrumento_id, q, limit, offset, facetas=False, filtros=None):
    instrumento = publico(db, instrumento_id, lock=True)
    if instrumento.geracao_publica != instrumento.geracao_indexada:
        raise HTTPException(503, "Indice publico em atualizacao. Tente novamente.")
    schema = db.get(PublicacaoInstrumento, instrumento.publicacao_id).schema_json
    campos = campos_publicos(db, schema)
    payload = {"q": q, "limit": limit, "offset": offset}
    allowed = {c["chave"] for c in campos if c.get("facetavel") or c.get("filtro_avancado")}
    clauses = []
    for key, value in (filtros or {}).items():
        if key not in allowed or not isinstance(value, (str, int, float, bool)):
            raise HTTPException(422, "Filtro publico invalido.")
        clauses.append(f"dados.{key} = {json.dumps(value, ensure_ascii=True)}")
    if clauses:
        payload["filter"] = clauses
    if facetas:
        payload["facets"] = [f"dados.{c['chave']}" for c in campos if c.get("facetavel")]
    try:
        response = _meili_request("POST", f"/indexes/{indice(instrumento)}/search", payload)
    except httpx.HTTPError as exc:
        raise HTTPException(503, "Busca publica temporariamente indisponivel.") from exc
    return {"items": response.get("hits", []), "total": response.get("estimatedTotalHits", 0),
            "limit": limit, "offset": offset, "facetas": response.get("facetDistribution", {})}


def aguardar(task):
    uid = task.get("taskUid")
    if uid is None:
        return
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        status = _meili_request("GET", f"/tasks/{uid}")
        if status["status"] == "succeeded":
            return
        if status["status"] in {"failed", "canceled"}:
            raise RuntimeError("Indexacao publica falhou.")
        time.sleep(.1)
    raise RuntimeError("Tempo limite da indexacao publica.")


def processar_pendente(db, batch_size=100, instrumento_id=None):
    query = select(IndexacaoJob).where(IndexacaoJob.tipo == "PUBLICACAO", IndexacaoJob.status == "PENDENTE")
    if instrumento_id:
        query = query.where(IndexacaoJob.instrumento_id == instrumento_id)
    job = db.scalar(query.order_by(IndexacaoJob.criado_em).with_for_update(skip_locked=True).limit(1))
    if not job:
        return False
    instrumento = db.get(Instrumento, job.instrumento_id)
    generation = job.geracao_publica
    if generation != instrumento.geracao_publica:
        job.status = "CONCLUIDO"
        db.commit()
        return True
    try:
        name = indice(instrumento)
        existing = _meili_request("GET", f"/indexes/{name}", allow_not_found=True)
        if not existing:
            aguardar(_meili_request("POST", "/indexes", {"uid": name, "primaryKey": "id"}, allow_conflict=True))
        public_schema = db.get(PublicacaoInstrumento, instrumento.publicacao_id) if instrumento.publicacao_id else None
        fields = campos_publicos(db, public_schema.schema_json) if public_schema else []
        aguardar(_meili_request("PATCH", f"/indexes/{name}/settings", {
            "searchableAttributes": ["texto_geral"], "displayedAttributes": ["*"],
            "filterableAttributes": [f"dados.{c['chave']}" for c in fields if c.get("facetavel") or c.get("filtro_avancado")]}))
        rows = []
        if instrumento.visibilidade == "PUBLICO" and public_schema and instrumento.status != "ARQUIVADO":
            query = select(EditorialRegistro).where(EditorialRegistro.instrumento_id == instrumento.id,
                EditorialRegistro.status_operacional == "ATIVO", EditorialRegistro.status_editorial != "ARQUIVADO",
                EditorialRegistro.snapshot_id.is_not(None))
            if job.ultimo_cursor_mongodb:
                query = query.where(EditorialRegistro.registro_id > job.ultimo_cursor_mongodb)
            rows = list(db.scalars(query.order_by(EditorialRegistro.registro_id).limit(batch_size + 1)))
        page = rows[:batch_size]
        snapshots = {d["_id"]: d for d in snapshots_collection().find(
            {"_id": {"$in": [r.snapshot_id for r in page]}}, {"imagens": 0})}
        schemas = {str(s.id): s.schema_json for s in db.scalars(select(PublicacaoInstrumento).where(
            PublicacaoInstrumento.id.in_([uuid.UUID(d["schema_id"]) for d in snapshots.values()])))}
        allowed = {c["chave"] for c in fields}
        documents = [projecao(db, snapshots[r.snapshot_id],
            [c for c in schemas[snapshots[r.snapshot_id]["schema_id"]]["campos"]
             if c.get("exibir_publico") and c["chave"] in allowed])
            for r in page if r.snapshot_id in snapshots and snapshots[r.snapshot_id]["schema_id"] in schemas]
        if len(documents) != len(page) or any(d is None for d in documents):
            raise RuntimeError("Snapshot publicado ausente.")
        if documents:
            aguardar(_meili_request("POST", f"/indexes/{name}/documents", documents))
            job.ultimo_cursor_mongodb = page[-1].registro_id
            job.processados += len(page)
        if len(rows) <= batch_size:
            # Check under a row lock before exposing a completed generation.
            db.refresh(instrumento, with_for_update=True)
            if instrumento.geracao_publica == generation:
                instrumento.geracao_indexada = generation
            job.status = "CONCLUIDO"
        db.commit()
    except Exception:
        logging.getLogger(__name__).exception("Falha no job publico %s", job.id)
        db.rollback()
        job = db.get(IndexacaoJob, job.id)
        job.status, job.erro = "FALHOU", "Falha na indexacao publica; reconciliacao necessaria."
        db.commit()
    return True
