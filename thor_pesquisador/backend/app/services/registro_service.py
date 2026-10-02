from __future__ import annotations

import json
import re
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pymongo.collection import Collection
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.mongo import registros_collection
from app.models.enums import StatusRegistro, TipoCampo
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.schemas.registro import RegistroCreate, RegistroOut, RegistroPage, RegistroUpdate


def criar_registro(db: Session, instrumento_id: uuid.UUID, payload: RegistroCreate, usuario_id: uuid.UUID | None, collection: Collection | None = None) -> RegistroOut:
    instrumento, campos = _schema(db, instrumento_id)
    _validar(campos, payload.dados)
    now = datetime.now(UTC)
    documento = {
        "_id": str(uuid.uuid4()),
        "instrumento_id": str(instrumento_id),
        "schema_version": instrumento.schema_version,
        "dados": payload.dados,
        "status": payload.status.value,
        "criado_por": str(usuario_id) if usuario_id else None,
        "atualizado_por": str(usuario_id) if usuario_id else None,
        "criado_em": now,
        "atualizado_em": now,
        "texto_busca_basico": _texto_busca(campos, payload.dados),
    }
    _collection(collection).insert_one(documento)
    return _to_out(documento)


def listar_registros(db: Session, instrumento_id: uuid.UUID, page_size: int = 50, cursor: str | None = None, collection: Collection | None = None) -> RegistroPage:
    _require_instrumento(db, instrumento_id)
    filtro: dict[str, Any] = {"instrumento_id": str(instrumento_id), "status": {"$ne": StatusRegistro.EXCLUIDO.value}}
    if cursor:
        data = _decode_cursor(cursor)
        filtro["$or"] = [{"criado_em": {"$lt": data["criado_em"]}}, {"criado_em": data["criado_em"], "_id": {"$lt": data["id"]}}]
    safe_size = min(max(page_size, 1), 100)
    docs = list(_collection(collection).find(filtro).sort([("criado_em", -1), ("_id", -1)]).limit(safe_size + 1))
    has_more = len(docs) > safe_size
    page_docs = docs[:safe_size]
    return RegistroPage(
        items=[_to_out(doc) for doc in page_docs],
        page_size=safe_size,
        has_more=has_more,
        next_cursor=_encode_cursor(page_docs[-1]) if has_more and page_docs else None,
    )


def buscar_registros(db: Session, instrumento_id: uuid.UUID, q: str, page_size: int = 50, cursor: str | None = None, collection: Collection | None = None) -> RegistroPage:
    _require_instrumento(db, instrumento_id)
    filtro: dict[str, Any] = {
        "instrumento_id": str(instrumento_id),
        "status": {"$ne": StatusRegistro.EXCLUIDO.value},
        "texto_busca_basico": {"$regex": re.escape(q.strip()), "$options": "i"},
    }
    if cursor:
        data = _decode_cursor(cursor)
        filtro["$and"] = [{"$or": [{"criado_em": {"$lt": data["criado_em"]}}, {"criado_em": data["criado_em"], "_id": {"$lt": data["id"]}}]}]
    safe_size = min(max(page_size, 1), 100)
    docs = list(_collection(collection).find(filtro).sort([("criado_em", -1), ("_id", -1)]).limit(safe_size + 1))
    has_more = len(docs) > safe_size
    page_docs = docs[:safe_size]
    return RegistroPage(
        items=[_to_out(doc) for doc in page_docs],
        page_size=safe_size,
        has_more=has_more,
        next_cursor=_encode_cursor(page_docs[-1]) if has_more and page_docs else None,
    )


def obter_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, collection: Collection | None = None) -> RegistroOut:
    _require_instrumento(db, instrumento_id)
    doc = _collection(collection).find_one({"_id": registro_id, "instrumento_id": str(instrumento_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return _to_out(doc)


def atualizar_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, payload: RegistroUpdate, usuario_id: uuid.UUID | None, collection: Collection | None = None) -> RegistroOut:
    _instrumento, campos = _schema(db, instrumento_id)
    _validar(campos, payload.dados)
    now = datetime.now(UTC)
    result = _collection(collection).find_one_and_update(
        {"_id": registro_id, "instrumento_id": str(instrumento_id)},
        {
            "$set": {
                "dados": payload.dados,
                "status": payload.status.value,
                "atualizado_por": str(usuario_id) if usuario_id else None,
                "atualizado_em": now,
                "texto_busca_basico": _texto_busca(campos, payload.dados),
            }
        },
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return _to_out(result)


def excluir_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, collection: Collection | None = None) -> None:
    _require_instrumento(db, instrumento_id)
    result = _collection(collection).update_one(
        {"_id": registro_id, "instrumento_id": str(instrumento_id)},
        {"$set": {"status": StatusRegistro.EXCLUIDO.value, "atualizado_em": datetime.now(UTC)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")


def _schema(db: Session, instrumento_id: uuid.UUID) -> tuple[Instrumento, list[InstrumentoCampo]]:
    instrumento = _require_instrumento(db, instrumento_id)
    campos = list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == instrumento_id).order_by(InstrumentoCampo.ordem.asc())))
    return instrumento, campos


def _require_instrumento(db: Session, instrumento_id: uuid.UUID) -> Instrumento:
    instrumento = db.get(Instrumento, instrumento_id)
    if not instrumento:
        raise HTTPException(status_code=404, detail="Instrumento nao encontrado.")
    return instrumento


def _validar(campos: list[InstrumentoCampo], dados: dict[str, Any]) -> None:
    by_key = {campo.chave: campo for campo in campos}
    unknown = sorted(set(dados) - set(by_key))
    if unknown:
        raise HTTPException(status_code=422, detail=f"Campos nao configurados: {', '.join(unknown)}")
    for campo in campos:
        value = dados.get(campo.chave)
        if campo.obrigatorio and _empty(value):
            raise HTTPException(status_code=422, detail=f"O campo '{campo.nome}' e obrigatorio.")
        if _empty(value):
            continue
        _validar_tipo(campo, value)


def _validar_tipo(campo: InstrumentoCampo, value: Any) -> None:
    tipo = TipoCampo(campo.tipo)
    if tipo in {TipoCampo.TEXTO_CURTO, TipoCampo.TEXTO_LONGO, TipoCampo.URL, TipoCampo.DATA, TipoCampo.LISTA_SIMPLES} and not isinstance(value, str):
        raise HTTPException(status_code=422, detail=f"O campo '{campo.nome}' deve ser texto.")
    if tipo == TipoCampo.NUMERO and (not isinstance(value, int | float) or isinstance(value, bool)):
        raise HTTPException(status_code=422, detail=f"O campo '{campo.nome}' deve ser numerico.")
    if tipo == TipoCampo.BOOLEANO and not isinstance(value, bool):
        raise HTTPException(status_code=422, detail=f"O campo '{campo.nome}' deve ser booleano.")
    if tipo == TipoCampo.LISTA_MULTIPLA and (not isinstance(value, list) or any(not isinstance(item, str) for item in value)):
        raise HTTPException(status_code=422, detail=f"O campo '{campo.nome}' deve ser uma lista de textos.")


def _texto_busca(campos: list[InstrumentoCampo], dados: dict[str, Any]) -> str:
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


def _empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def _collection(collection: Collection | None) -> Collection:
    return collection if collection is not None else registros_collection()


def _to_out(doc: dict[str, Any]) -> RegistroOut:
    return RegistroOut(
        id=doc["_id"],
        instrumento_id=doc["instrumento_id"],
        schema_version=doc.get("schema_version", 1),
        dados=doc.get("dados", {}),
        status=doc.get("status", StatusRegistro.ATIVO.value),
        criado_por=doc.get("criado_por"),
        atualizado_por=doc.get("atualizado_por"),
        criado_em=doc["criado_em"],
        atualizado_em=doc["atualizado_em"],
    )


def _encode_cursor(doc: dict[str, Any]) -> str:
    payload = json.dumps({"criado_em": doc["criado_em"].isoformat(), "id": doc["_id"]}, separators=(",", ":")).encode()
    return urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _decode_cursor(cursor: str) -> dict[str, Any]:
    payload = json.loads(urlsafe_b64decode((cursor + "=" * (-len(cursor) % 4)).encode()).decode())
    criado_em = datetime.fromisoformat(payload["criado_em"])
    if criado_em.tzinfo is None:
        criado_em = criado_em.replace(tzinfo=UTC)
    return {"criado_em": criado_em, "id": payload["id"]}
