from __future__ import annotations

import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as BinasciiError
from datetime import UTC, datetime
import json
import re
from typing import Any

from pymongo import ReturnDocument
from pymongo.collection import Collection
from sqlalchemy.orm import Session

from app.db.mongo import get_instrumento_registros_collection
from app.models.enums import TipoCampoInstrumento
from app.models.instrumento_pesquisa import InstrumentoCampo, InstrumentoPesquisa
from app.schemas.instrumento_registro import (
    InstrumentoRegistroCreate,
    InstrumentoRegistroOut,
    InstrumentoRegistroPage,
    InstrumentoRegistroUpdate,
    StatusInstrumentoRegistro,
)
from app.services.instrumento_search_service import InstrumentoSearchService


class InstrumentoRegistroService:
    @staticmethod
    def criar(
        db: Session,
        instrumento_id: uuid.UUID,
        dados: InstrumentoRegistroCreate,
        collection: Collection | None = None,
    ) -> InstrumentoRegistroOut:
        campos = InstrumentoRegistroService._schema_campos(db, instrumento_id)
        InstrumentoRegistroService._validar_dados(campos, dados.dados)

        now = datetime.now(UTC)
        documento = {
            "_id": str(uuid.uuid4()),
            "instrumento_id": str(instrumento_id),
            "schema_version": 1,
            "dados": dados.dados,
            "unidade_acondicionamento_ids": dados.unidade_acondicionamento_ids,
            "registro_descritivo_ids": dados.registro_descritivo_ids,
            "status": dados.status.value,
            "criado_em": now,
            "atualizado_em": now,
        }

        target_collection = InstrumentoRegistroService._collection(collection)
        target_collection.insert_one(documento)
        try:
            InstrumentoSearchService.indexar_registro(documento)
        except Exception:
            target_collection.delete_one({"_id": documento["_id"]})
            raise
        return InstrumentoRegistroService._to_out(documento)

    @staticmethod
    def listar(
        db: Session,
        instrumento_id: uuid.UUID,
        status: StatusInstrumentoRegistro | None = None,
        page_size: int = 50,
        cursor: str | None = None,
        collection: Collection | None = None,
    ) -> InstrumentoRegistroPage:
        InstrumentoRegistroService._validar_instrumento(db, instrumento_id)
        filtro: dict[str, Any] = {"instrumento_id": str(instrumento_id)}
        if status:
            filtro["status"] = status.value
        else:
            filtro["status"] = {"$ne": StatusInstrumentoRegistro.EXCLUIDO.value}

        if cursor:
            cursor_data = InstrumentoRegistroService._decode_cursor(cursor)
            filtro["$or"] = [
                {"criado_em": {"$lt": cursor_data["criado_em"]}},
                {"criado_em": cursor_data["criado_em"], "_id": {"$lt": cursor_data["id"]}},
            ]

        safe_page_size = min(max(page_size, 1), 100)
        documentos = list(
            InstrumentoRegistroService._collection(collection)
            .find(filtro)
            .sort([("criado_em", -1), ("_id", -1)])
            .limit(safe_page_size + 1)
        )
        has_more = len(documentos) > safe_page_size
        page_documents = documentos[:safe_page_size]
        next_cursor = (
            InstrumentoRegistroService._encode_cursor(page_documents[-1])
            if has_more and page_documents
            else None
        )
        return InstrumentoRegistroPage(
            items=[InstrumentoRegistroService._to_out(documento) for documento in page_documents],
            page_size=safe_page_size,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def buscar(
        db: Session,
        instrumento_id: uuid.UUID,
        q: str,
        page_size: int = 50,
        cursor: str | None = None,
        collection: Collection | None = None,
    ) -> InstrumentoRegistroPage:
        campos = InstrumentoRegistroService._schema_campos(db, instrumento_id)
        campos_busca = [campo for campo in campos if campo.aparece_busca]
        termo = q.strip()
        safe_page_size = min(max(page_size, 1), 100)

        filtro: dict[str, Any] = {
            "instrumento_id": str(instrumento_id),
            "status": {"$ne": StatusInstrumentoRegistro.EXCLUIDO.value},
        }

        if termo and campos_busca:
            escaped = re.escape(termo)
            filtro["$or"] = [
                {f"dados.{campo.chave}": {"$regex": escaped, "$options": "i"}}
                for campo in campos_busca
            ]
        elif termo:
            return InstrumentoRegistroPage(items=[], page_size=safe_page_size)

        if cursor:
            cursor_data = InstrumentoRegistroService._decode_cursor(cursor)
            cursor_filter = [
                {"criado_em": {"$lt": cursor_data["criado_em"]}},
                {"criado_em": cursor_data["criado_em"], "_id": {"$lt": cursor_data["id"]}},
            ]
            if "$or" in filtro:
                filtro["$and"] = [{"$or": filtro.pop("$or")}, {"$or": cursor_filter}]
            else:
                filtro["$or"] = cursor_filter

        documentos = list(
            InstrumentoRegistroService._collection(collection)
            .find(filtro)
            .sort([("criado_em", -1), ("_id", -1)])
            .limit(safe_page_size + 1)
        )
        has_more = len(documentos) > safe_page_size
        page_documents = documentos[:safe_page_size]
        next_cursor = (
            InstrumentoRegistroService._encode_cursor(page_documents[-1])
            if has_more and page_documents
            else None
        )
        return InstrumentoRegistroPage(
            items=[InstrumentoRegistroService._to_out(documento) for documento in page_documents],
            page_size=safe_page_size,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def obter(
        db: Session,
        instrumento_id: uuid.UUID,
        registro_id: str,
        collection: Collection | None = None,
    ) -> InstrumentoRegistroOut | None:
        InstrumentoRegistroService._validar_instrumento(db, instrumento_id)
        documento = InstrumentoRegistroService._collection(collection).find_one(
            {
                "_id": registro_id,
                "instrumento_id": str(instrumento_id),
            }
        )
        return InstrumentoRegistroService._to_out(documento) if documento else None

    @staticmethod
    def atualizar(
        db: Session,
        instrumento_id: uuid.UUID,
        registro_id: str,
        dados: InstrumentoRegistroUpdate,
        collection: Collection | None = None,
    ) -> InstrumentoRegistroOut | None:
        campos = InstrumentoRegistroService._schema_campos(db, instrumento_id)
        InstrumentoRegistroService._validar_dados(campos, dados.dados)

        collection = InstrumentoRegistroService._collection(collection)
        now = datetime.now(UTC)
        result = collection.find_one_and_update(
            {
                "_id": registro_id,
                "instrumento_id": str(instrumento_id),
            },
            {
                "$set": {
                    "dados": dados.dados,
                    "unidade_acondicionamento_ids": dados.unidade_acondicionamento_ids,
                    "registro_descritivo_ids": dados.registro_descritivo_ids,
                    "status": dados.status.value,
                    "atualizado_em": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if result:
            InstrumentoSearchService.indexar_registro(result)
        return InstrumentoRegistroService._to_out(result) if result else None

    @staticmethod
    def excluir(
        db: Session,
        instrumento_id: uuid.UUID,
        registro_id: str,
        collection: Collection | None = None,
    ) -> bool:
        InstrumentoRegistroService._validar_instrumento(db, instrumento_id)
        result = InstrumentoRegistroService._collection(collection).update_one(
            {
                "_id": registro_id,
                "instrumento_id": str(instrumento_id),
            },
            {
                "$set": {
                    "status": StatusInstrumentoRegistro.EXCLUIDO.value,
                    "atualizado_em": datetime.now(UTC),
                }
            },
        )
        if result.matched_count:
            InstrumentoSearchService.remover_registro(instrumento_id, registro_id)
        return result.matched_count > 0

    @staticmethod
    def _schema_campos(db: Session, instrumento_id: uuid.UUID) -> list[InstrumentoCampo]:
        InstrumentoRegistroService._validar_instrumento(db, instrumento_id)
        return (
            db.query(InstrumentoCampo)
            .filter(InstrumentoCampo.instrumento_id == instrumento_id)
            .order_by(InstrumentoCampo.ordem.asc())
            .all()
        )

    @staticmethod
    def _validar_instrumento(db: Session, instrumento_id: uuid.UUID) -> None:
        if db.get(InstrumentoPesquisa, instrumento_id) is None:
            raise LookupError("Instrumento de pesquisa não encontrado.")

    @staticmethod
    def _validar_dados(campos: list[InstrumentoCampo], dados: dict[str, Any]) -> None:
        campos_por_chave = {campo.chave: campo for campo in campos}

        for campo in campos:
            valor = dados.get(campo.chave)
            if campo.obrigatorio and InstrumentoRegistroService._is_empty(valor):
                raise ValueError(f"O campo '{campo.nome}' é obrigatório.")

            if InstrumentoRegistroService._is_empty(valor):
                continue

            InstrumentoRegistroService._validar_tipo(campo, valor)

        desconhecidos = sorted(set(dados.keys()) - set(campos_por_chave.keys()))
        if desconhecidos:
            raise ValueError(
                "Campos não configurados para o instrumento: "
                + ", ".join(desconhecidos)
            )

    @staticmethod
    def _validar_tipo(campo: InstrumentoCampo, valor: Any) -> None:
        tipo = campo.tipo
        if tipo in {TipoCampoInstrumento.TEXTO_CURTO, TipoCampoInstrumento.TEXTO_LONGO, TipoCampoInstrumento.URL}:
            if not isinstance(valor, str):
                raise ValueError(f"O campo '{campo.nome}' deve ser texto.")
        elif tipo == TipoCampoInstrumento.NUMERO:
            if not isinstance(valor, int | float) or isinstance(valor, bool):
                raise ValueError(f"O campo '{campo.nome}' deve ser numérico.")
        elif tipo == TipoCampoInstrumento.DATA:
            if not isinstance(valor, str):
                raise ValueError(f"O campo '{campo.nome}' deve ser uma data em texto ISO.")
        elif tipo == TipoCampoInstrumento.BOOLEANO:
            if not isinstance(valor, bool):
                raise ValueError(f"O campo '{campo.nome}' deve ser booleano.")
        elif tipo == TipoCampoInstrumento.LISTA_SIMPLES:
            if not isinstance(valor, str):
                raise ValueError(f"O campo '{campo.nome}' deve conter uma opção.")
        elif tipo == TipoCampoInstrumento.LISTA_MULTIPLA:
            if not isinstance(valor, list) or any(not isinstance(item, str) for item in valor):
                raise ValueError(f"O campo '{campo.nome}' deve conter uma lista de opções.")

    @staticmethod
    def _is_empty(valor: Any) -> bool:
        return valor is None or valor == "" or valor == []

    @staticmethod
    def _collection(collection: Collection | None) -> Collection:
        return collection if collection is not None else get_instrumento_registros_collection()

    @staticmethod
    def _to_out(documento: dict[str, Any]) -> InstrumentoRegistroOut:
        return InstrumentoRegistroOut(
            id=documento["_id"],
            instrumento_id=documento["instrumento_id"],
            schema_version=documento["schema_version"],
            dados=documento.get("dados", {}),
            unidade_acondicionamento_ids=documento.get("unidade_acondicionamento_ids", []),
            registro_descritivo_ids=documento.get("registro_descritivo_ids", []),
            status=documento.get("status", StatusInstrumentoRegistro.ATIVO.value),
            criado_em=documento["criado_em"],
            atualizado_em=documento["atualizado_em"],
        )

    @staticmethod
    def _encode_cursor(documento: dict[str, Any]) -> str:
        payload = {
            "criado_em": documento["criado_em"].isoformat(),
            "id": documento["_id"],
        }
        encoded = urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        return encoded.decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> dict[str, Any]:
        try:
            padded = cursor + ("=" * (-len(cursor) % 4))
            payload = json.loads(urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
            criado_em = datetime.fromisoformat(payload["criado_em"])
            if criado_em.tzinfo is None:
                criado_em = criado_em.replace(tzinfo=UTC)
            return {
                "criado_em": criado_em,
                "id": str(payload["id"]),
            }
        except (BinasciiError, KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
            raise ValueError("Cursor de paginação inválido.") from e
