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
from app.services.instrumento_indexing_events import InstrumentoIndexingEventPublisher
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

        InstrumentoRegistroService._collection(collection).insert_one(documento)
        InstrumentoIndexingEventPublisher.registro_criado(instrumento_id, documento["_id"])
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
    def buscar_avancado(
        db: Session,
        instrumento_id: uuid.UUID,
        q: str | None = "",
        filters: dict[str, Any] | None = None,
        sort: list[dict[str, str]] | None = None,
        page_size: int = 50,
        cursor: str | None = None,
    ) -> InstrumentoRegistroPage:
        campos = InstrumentoRegistroService._schema_campos(db, instrumento_id)
        filtros_por_chave = {campo.chave: campo for campo in campos if campo.filtro_avancado}
        ordenaveis = {campo.chave for campo in campos if campo.ordenavel}

        meili_filters = ["status != EXCLUIDO"]
        for chave, valor in (filters or {}).items():
            if chave not in filtros_por_chave:
                raise ValueError(f"O campo '{chave}' não está configurado para filtro avançado.")
            meili_filters.append(InstrumentoRegistroService._advanced_filter(filtros_por_chave[chave], valor))

        meili_sort: list[str] = []
        for item in sort or []:
            for chave, direction in item.items():
                if chave not in ordenaveis:
                    raise ValueError(f"O campo '{chave}' não está configurado para ordenação.")
                normalized_direction = direction.lower()
                if normalized_direction not in {"asc", "desc"}:
                    raise ValueError("A ordenação deve usar 'asc' ou 'desc'.")
                meili_sort.append(f"dados.{chave}:{normalized_direction}")

        safe_page_size = min(max(page_size, 1), 100)
        InstrumentoSearchService.configure_dynamic_fields(
            instrumento_id,
            filterable_fields=list(filtros_por_chave.keys()),
            sortable_fields=list(ordenaveis),
        )
        result = InstrumentoSearchService.buscar_avancado(
            instrumento_id,
            q=q,
            filtros=meili_filters,
            sort=meili_sort,
            page_size=safe_page_size,
            cursor=cursor,
        )

        return InstrumentoRegistroPage(
            items=[InstrumentoRegistroService._indexed_hit_to_out(hit) for hit in result["hits"]],
            page_size=safe_page_size,
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
        )

    @staticmethod
    def listar_facetas(
        db: Session,
        instrumento_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        campos = InstrumentoRegistroService._schema_campos(db, instrumento_id)
        facet_fields = [
            campo.chave
            for campo in campos
            if campo.filtro_avancado and campo.facetavel
        ]
        sortable_fields = [campo.chave for campo in campos if campo.ordenavel]
        if not facet_fields:
            return []

        InstrumentoSearchService.configure_dynamic_fields(
            instrumento_id,
            filterable_fields=[
                campo.chave
                for campo in campos
                if campo.filtro_avancado
            ],
            sortable_fields=sortable_fields,
        )
        distribution = InstrumentoSearchService.facet_distribution(instrumento_id, facet_fields)
        return [
            {
                "campo": field,
                "values": [
                    {"value": str(value), "count": int(count)}
                    for value, count in sorted(
                        distribution.get(field, {}).items(),
                        key=lambda item: str(item[0]).lower(),
                    )
                ],
            }
            for field in facet_fields
        ]

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
            InstrumentoIndexingEventPublisher.registro_atualizado(instrumento_id, registro_id)
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
            InstrumentoIndexingEventPublisher.registro_excluido(instrumento_id, registro_id)
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
    def _advanced_filter(campo: InstrumentoCampo, valor: Any) -> str:
        chave = campo.chave
        attr = f"dados.{chave}"
        if isinstance(valor, list):
            values = [
                InstrumentoRegistroService._meili_value_for_campo(campo, item)
                for item in valor
                if item not in (None, "")
            ]
            if not values:
                raise ValueError(f"O filtro '{chave}' não possui valores.")
            return "(" + " OR ".join(f"{attr} = {item}" for item in values) + ")"

        if isinstance(valor, dict):
            parts = []
            if valor.get("gte") not in (None, ""):
                parts.append(f"{attr} >= {InstrumentoRegistroService._meili_value_for_campo(campo, valor['gte'])}")
            if valor.get("lte") not in (None, ""):
                parts.append(f"{attr} <= {InstrumentoRegistroService._meili_value_for_campo(campo, valor['lte'])}")
            if not parts:
                raise ValueError(f"O filtro '{chave}' não possui limites.")
            return " AND ".join(parts)

        return f"{attr} = {InstrumentoRegistroService._meili_value_for_campo(campo, valor)}"

    @staticmethod
    def _meili_value_for_campo(campo: InstrumentoCampo, value: Any) -> str:
        if campo.tipo == TipoCampoInstrumento.NUMERO and isinstance(value, str):
            try:
                number = float(value) if "." in value else int(value)
            except ValueError:
                raise ValueError(f"O filtro '{campo.nome}' deve ser numÃ©rico.") from None
            return InstrumentoRegistroService._meili_value(number)
        return InstrumentoRegistroService._meili_value(value)

    @staticmethod
    def _meili_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int | float) and not isinstance(value, bool):
            return str(value)
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

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
    def _indexed_hit_to_out(hit: dict[str, Any]) -> InstrumentoRegistroOut:
        return InstrumentoRegistroOut(
            id=hit["id"],
            instrumento_id=hit["instrumento_id"],
            schema_version=hit.get("schema_version", 1),
            dados=hit.get("dados", {}),
            unidade_acondicionamento_ids=hit.get("unidade_acondicionamento_ids", []),
            registro_descritivo_ids=hit.get("registro_descritivo_ids", []),
            status=hit.get("status", StatusInstrumentoRegistro.ATIVO.value),
            criado_em=datetime.fromisoformat(hit["criado_em"].replace("Z", "+00:00")),
            atualizado_em=datetime.fromisoformat(
                hit.get("atualizado_em", hit["criado_em"]).replace("Z", "+00:00")
            ),
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
