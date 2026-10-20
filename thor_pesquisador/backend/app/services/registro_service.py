from __future__ import annotations

import json
import re
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from pymongo.collection import Collection
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.mongo import registros_collection
from app.models.enums import StatusRegistro, TipoCampo
from app.models.instrumento import Instrumento, InstrumentoCampo
from app.schemas.registro import RegistroCreate, RegistroOut, RegistroPage, RegistroUpdate, RegistroConsulta, RegistroConsultaPage
from app.services.indexacao_service import enqueue_registro
from app.services.permissao_service import require
from app.services.editorial_service import controle, invalidar_publicacao, auditar_edicao
from app.models.editorial import EditorialRegistro


def criar_registro(db: Session, instrumento_id: uuid.UUID, payload: RegistroCreate, usuario_id: uuid.UUID | None, collection: Collection | None = None) -> RegistroOut:
    require(db, "registros_incluir", instrumento_id)
    if payload.status and payload.status.value == "EXCLUIDO":
        require(db, "registros_excluir", instrumento_id)
    instrumento, campos = _schema(db, instrumento_id)
    _validar(campos, payload.dados)
    now = datetime.now(UTC)
    documento = {
        "_id": str(uuid.uuid4()),
        "_revision": 1,
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
    from app.services.auditoria_service import registrar
    operacao = uuid.uuid4()
    registrar(db, "CRIAR_REGISTRO_INTENCAO", "registro", documento["_id"], instrumento_id,
              documento["_id"], {"etapa": "INTENCAO_PERSISTIDA"}, operacao_id=operacao)
    db.execute(update(Instrumento).where(Instrumento.id == instrumento_id)
               .values(revisao_dados=Instrumento.revisao_dados + 1).execution_options(synchronize_session=False))
    db.commit()
    _collection(collection).insert_one(documento)
    controle(db, instrumento_id, documento["_id"], documento)
    registrar(db, "CRIAR_REGISTRO_CONCLUIDO", "registro", documento["_id"], instrumento_id,
              documento["_id"], {"etapa": "CONCLUIDA"}, operacao_id=operacao)
    db.commit()
    enqueue_registro(instrumento_id, documento["_id"])
    return _to_out(documento, db)


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
        items=_pagina_out(db, instrumento_id, page_docs),
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
        items=_pagina_out(db, instrumento_id, page_docs),
        page_size=safe_size,
        has_more=has_more,
        next_cursor=_encode_cursor(page_docs[-1]) if has_more and page_docs else None,
    )


def consultar_registros(db: Session, instrumento_id: uuid.UUID, payload: RegistroConsulta,
                       collection: Collection | None = None) -> RegistroConsultaPage:
    _require_instrumento(db, instrumento_id)
    filtro: dict[str, Any] = {"instrumento_id": str(instrumento_id),
                              "status": {"$ne": StatusRegistro.EXCLUIDO.value}}
    if payload.status is not None:
        if payload.status == StatusRegistro.EXCLUIDO:
            raise HTTPException(422, "Registros excluidos nao fazem parte da consulta operacional.")
        filtro["status"] = payload.status.value
    if payload.q.strip():
        filtro["texto_busca_basico"] = {"$regex": re.escape(payload.q.strip()), "$options": "i"}
    if payload.filtros:
        campos = {c.chave: c for c in db.scalars(select(InstrumentoCampo).where(
            InstrumentoCampo.instrumento_id == instrumento_id, InstrumentoCampo.aparece_busca.is_(True)))}
        for chave, valor in payload.filtros.items():
            campo = campos.get(chave)
            if campo is None:
                raise HTTPException(422, "Filtro nao disponivel no instrumento.")
            if _empty(valor):
                continue
            _validar_tipo(campo, valor)
            if campo.tipo in {TipoCampo.NUMERO, TipoCampo.BOOLEANO}:
                filtro["dados." + chave] = valor
            elif campo.tipo == TipoCampo.LISTA_MULTIPLA:
                filtro["dados." + chave] = {"$all": valor}
            elif campo.tipo in {TipoCampo.DATA, TipoCampo.LISTA_SIMPLES}:
                filtro["dados." + chave] = valor
            else:
                filtro["dados." + chave] = {"$regex": re.escape(valor.strip()), "$options": "i"}
    coll = _collection(collection)
    total = coll.count_documents(filtro)
    docs = list(coll.find(filtro).sort([("criado_em", -1), ("_id", -1)])
                .skip(payload.offset).limit(payload.limit))
    return RegistroConsultaPage(items=_pagina_out(db, instrumento_id, docs), total=total,
                                limit=payload.limit, offset=payload.offset)


def obter_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, collection: Collection | None = None, consultar=True) -> RegistroOut:
    _require_instrumento(db, instrumento_id, consultar=consultar)
    doc = _collection(collection).find_one({"_id": registro_id, "instrumento_id": str(instrumento_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    return _to_out(doc, db)


def atualizar_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, payload: RegistroUpdate, usuario_id: uuid.UUID | None, collection: Collection | None = None) -> RegistroOut:
    require(db, "registros_editar", instrumento_id)
    if payload.status and payload.status.value == "EXCLUIDO":
        require(db, "registros_excluir", instrumento_id)
    _instrumento, campos = _schema(db, instrumento_id)
    _validar(campos, payload.dados)
    db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    doc = _collection(collection).find_one({"_id": registro_id, "instrumento_id": str(instrumento_id)})
    if not doc:
        raise HTTPException(404, "Registro nao encontrado.")
    row = controle(db, instrumento_id, registro_id, doc)
    if row.status_operacional == "EXCLUIDO" or row.status_editorial == "ARQUIVADO":
        raise HTTPException(409, "Registro excluido ou arquivado nao pode ser editado diretamente.")
    actual = doc.get("_revision", 1)
    if row.versao != actual:
        raise HTTPException(409, "Registro necessita reconciliacao antes de editar.")
    if payload.versao is not None and payload.versao != actual:
        raise HTTPException(409, "Versao alterada. Recarregue o registro.")
    if (row.status_editorial != "RASCUNHO" or row.snapshot_id) and payload.versao is None:
        raise HTTPException(409, "Informe a versao ao editar registro com historico editorial.")
    anterior = row.status_editorial
    row.versao = actual + 1
    row.status_editorial = "RASCUNHO"
    row.status_operacional = payload.status.value
    # Commit the revocation intent before touching Mongo. Failure cannot expose an inactive draft.
    invalidar_publicacao(db, _instrumento)
    operation = auditar_edicao(db, instrumento_id, registro_id, "iniciar_edicao", anterior, "RASCUNHO", row.versao,
        {"etapa": "INTENCAO_PERSISTIDA", "status_operacional": row.status_operacional})
    db.commit()
    now = datetime.now(UTC)
    result = _collection(collection).find_one_and_update(
        {"_id": registro_id, "instrumento_id": str(instrumento_id),
         **({"_revision": actual} if "_revision" in doc else {"_revision": {"$exists": False}})},
        {
            "$set": {
                "_revision": row.versao,
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
        db.rollback()
        raise HTTPException(status_code=409, detail="Registro alterado por outra operacao.")
    if payload.status == StatusRegistro.EXCLUIDO:
        from app.services.imagem_service import limpar_vinculos
        limpar_vinculos(db, instrumento_id, registro_id, usuario_id)
    auditar_edicao(db, instrumento_id, registro_id, "concluir_edicao", "RASCUNHO", "RASCUNHO", row.versao,
                   {"operacao_relacionada_id": str(operation), "etapa": "CONCLUIDA"})
    db.commit()
    enqueue_registro(instrumento_id, registro_id)
    return _to_out(result, db)


def excluir_registro(db: Session, instrumento_id: uuid.UUID, registro_id: str, collection: Collection | None = None, usuario_id=None) -> None:
    require(db, "registros_excluir", instrumento_id)
    _require_instrumento(db, instrumento_id, consultar=False)
    db.scalar(select(Instrumento).where(Instrumento.id == instrumento_id).with_for_update())
    doc = _collection(collection).find_one({"_id": registro_id, "instrumento_id": str(instrumento_id)})
    if not doc:
        raise HTTPException(404, "Registro nao encontrado.")
    row = controle(db, instrumento_id, registro_id, doc)
    anterior = row.status_editorial
    row.status_operacional = "EXCLUIDO"
    row.status_editorial = "ARQUIVADO"
    row.snapshot_id = None
    invalidar_publicacao(db, db.get(Instrumento, instrumento_id))
    auditar_edicao(db, instrumento_id, registro_id, "excluir_registro", anterior, "ARQUIVADO", row.versao,
                   {"etapa": "REVOGACAO_PERSISTIDA"})
    db.commit()
    result = _collection(collection).update_one(
        {"_id": registro_id, "instrumento_id": str(instrumento_id)},
        {"$set": {"status": StatusRegistro.EXCLUIDO.value, "atualizado_em": datetime.now(UTC)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Registro nao encontrado.")
    from app.services.imagem_service import limpar_vinculos
    limpar_vinculos(db, instrumento_id, registro_id, usuario_id)
    db.commit()
    enqueue_registro(instrumento_id, registro_id, acao="delete")


def _schema(db: Session, instrumento_id: uuid.UUID) -> tuple[Instrumento, list[InstrumentoCampo]]:
    instrumento = _require_instrumento(db, instrumento_id, consultar=False)
    db.refresh(instrumento, with_for_update=True)
    campos = list(db.scalars(select(InstrumentoCampo).where(InstrumentoCampo.instrumento_id == instrumento_id).order_by(InstrumentoCampo.ordem.asc())))
    return instrumento, campos


def _require_instrumento(db: Session, instrumento_id: uuid.UUID, consultar=True) -> Instrumento:
    if consultar:
        require(db, "registros_consultar", instrumento_id)
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


def _pagina_out(db, instrumento_id, docs):
    rows = db.scalars(select(EditorialRegistro).where(EditorialRegistro.instrumento_id == instrumento_id,
        EditorialRegistro.registro_id.in_([d["_id"] for d in docs]))).all()
    by_id = {r.registro_id: r for r in rows}
    return [_to_out(d, row=by_id.get(d["_id"])) for d in docs]


def _to_out(doc: dict[str, Any], db=None, row=None) -> RegistroOut:
    if db is not None:
        row = db.scalar(select(EditorialRegistro).where(
            EditorialRegistro.instrumento_id == uuid.UUID(doc["instrumento_id"]),
            EditorialRegistro.registro_id == doc["_id"]))
    return RegistroOut(
        id=doc["_id"],
        instrumento_id=doc["instrumento_id"],
        schema_version=doc.get("schema_version", 1),
        versao=row.versao if row else doc.get("_revision", 1),
        status_editorial=row.status_editorial if row else "RASCUNHO",
        versao_publicada=row.versao_publicada if row else None,
        dados=doc.get("dados", {}),
        status=row.status_operacional if row else doc.get("status", StatusRegistro.ATIVO.value),
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
