from __future__ import annotations

from datetime import UTC, datetime
from base64 import urlsafe_b64decode, urlsafe_b64encode
import json
import time
from typing import Any
import uuid

import httpx

from app.core.config import settings


class InstrumentoSearchService:
    @staticmethod
    def indexar_registro(documento: dict[str, Any]) -> None:
        index_uid = InstrumentoSearchService.index_uid(documento["instrumento_id"])
        payload = InstrumentoSearchService.to_index_document(documento)

        with InstrumentoSearchService.client() as client:
            InstrumentoSearchService.ensure_index(client, index_uid)
            response = client.post(
                f"/indexes/{index_uid}/documents",
                json=[payload],
            )
            response.raise_for_status()
            InstrumentoSearchService.wait_task(client, response.json().get("taskUid"))

    @staticmethod
    def remover_registro(instrumento_id: uuid.UUID | str, registro_id: str) -> None:
        index_uid = InstrumentoSearchService.index_uid(str(instrumento_id))

        with InstrumentoSearchService.client() as client:
            response = client.delete(f"/indexes/{index_uid}/documents/{registro_id}")
            if response.status_code not in {200, 202, 204, 404}:
                response.raise_for_status()
            if response.status_code in {200, 202}:
                InstrumentoSearchService.wait_task(client, response.json().get("taskUid"))

    @staticmethod
    def buscar_avancado(
        instrumento_id: uuid.UUID | str,
        q: str | None,
        filtros: list[str],
        sort: list[str],
        page_size: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        index_uid = InstrumentoSearchService.index_uid(str(instrumento_id))
        offset = InstrumentoSearchService.decode_offset(cursor)

        payload: dict[str, Any] = {
            "q": q or "",
            "limit": page_size,
            "offset": offset,
            "filter": filtros,
        }
        if sort:
            payload["sort"] = sort

        with InstrumentoSearchService.client() as client:
            response = client.post(f"/indexes/{index_uid}/search", json=payload)
            response.raise_for_status()
            data = response.json()

        next_offset = offset + len(data.get("hits", []))
        estimated_total = data.get("estimatedTotalHits") or 0
        return {
            "hits": data.get("hits", []),
            "next_cursor": (
                InstrumentoSearchService.encode_offset(next_offset)
                if next_offset < estimated_total
                else None
            ),
            "has_more": next_offset < estimated_total,
        }

    @staticmethod
    def facet_distribution(
        instrumento_id: uuid.UUID | str,
        facet_fields: list[str],
    ) -> dict[str, dict[str, int]]:
        if not facet_fields:
            return {}

        index_uid = InstrumentoSearchService.index_uid(str(instrumento_id))
        facet_attrs = [f"dados.{field}" for field in facet_fields]

        with InstrumentoSearchService.client() as client:
            response = client.post(
                f"/indexes/{index_uid}/search",
                json={
                    "q": "",
                    "limit": 0,
                    "filter": ["status != EXCLUIDO"],
                    "facets": facet_attrs,
                },
            )
            response.raise_for_status()
            data = response.json()

        distribution = data.get("facetDistribution") or {}
        return {
            field: distribution.get(f"dados.{field}", {})
            for field in facet_fields
        }

    @staticmethod
    def ensure_index(client: httpx.Client, index_uid: str) -> None:
        response = client.get(f"/indexes/{index_uid}")
        if response.status_code == 200:
            return
        if response.status_code != 404:
            response.raise_for_status()

        create_response = client.post(
            "/indexes",
            json={"uid": index_uid, "primaryKey": "id"},
        )
        create_response.raise_for_status()
        InstrumentoSearchService.wait_task(client, create_response.json().get("taskUid"))

        settings_response = client.patch(
            f"/indexes/{index_uid}/settings",
            json={
                "searchableAttributes": ["titulo", "texto_geral"],
                "filterableAttributes": [
                    "instrumento_id",
                    "schema_version",
                    "status",
                    "unidade_acondicionamento_ids",
                    "registro_descritivo_ids",
                ],
                "sortableAttributes": ["criado_em"],
            },
        )
        settings_response.raise_for_status()
        InstrumentoSearchService.wait_task(client, settings_response.json().get("taskUid"))

    @staticmethod
    def configure_dynamic_fields(
        instrumento_id: uuid.UUID | str,
        filterable_fields: list[str],
        sortable_fields: list[str],
    ) -> None:
        index_uid = InstrumentoSearchService.index_uid(str(instrumento_id))
        filterable = [
            "instrumento_id",
            "schema_version",
            "status",
            "unidade_acondicionamento_ids",
            "registro_descritivo_ids",
            *[f"dados.{field}" for field in filterable_fields],
        ]
        sortable = ["criado_em", *[f"dados.{field}" for field in sortable_fields]]

        with InstrumentoSearchService.client() as client:
            InstrumentoSearchService.ensure_index(client, index_uid)
            response = client.patch(
                f"/indexes/{index_uid}/settings",
                json={
                    "filterableAttributes": filterable,
                    "sortableAttributes": sortable,
                },
            )
            response.raise_for_status()
            InstrumentoSearchService.wait_task(client, response.json().get("taskUid"))

    @staticmethod
    def wait_task(client: httpx.Client, task_uid: int | None) -> None:
        if task_uid is None:
            return

        for _ in range(50):
            response = client.get(f"/tasks/{task_uid}")
            response.raise_for_status()
            task = response.json()
            status = task.get("status")
            if status == "succeeded":
                return
            if status == "failed":
                raise RuntimeError(f"Meilisearch task failed: {task}")
            time.sleep(0.1)

        raise TimeoutError(f"Timed out waiting for Meilisearch task {task_uid}")

    @staticmethod
    def to_index_document(documento: dict[str, Any]) -> dict[str, Any]:
        dados = documento.get("dados", {})
        titulo = InstrumentoSearchService.titulo_documento(dados)
        return {
            "id": documento["_id"],
            "instrumento_id": documento["instrumento_id"],
            "schema_version": documento.get("schema_version", 1),
            "titulo": titulo,
            "texto_geral": InstrumentoSearchService.texto_geral(dados),
            "dados": dados,
            "unidade_acondicionamento_ids": documento.get("unidade_acondicionamento_ids", []),
            "registro_descritivo_ids": documento.get("registro_descritivo_ids", []),
            "status": documento.get("status", "ATIVO"),
            "criado_em": InstrumentoSearchService.iso_utc(documento["criado_em"]),
            "atualizado_em": InstrumentoSearchService.iso_utc(documento["atualizado_em"]),
        }

    @staticmethod
    def titulo_documento(dados: dict[str, Any]) -> str:
        for chave in ("titulo", "titulo_item", "titulo_cartografico", "nome"):
            valor = dados.get(chave)
            if valor:
                return str(valor)

        for valor in dados.values():
            if valor:
                return InstrumentoSearchService.valor_texto(valor)

        return "Registro sem titulo"

    @staticmethod
    def texto_geral(dados: dict[str, Any]) -> str:
        return " ".join(
            texto
            for texto in (InstrumentoSearchService.valor_texto(valor) for valor in dados.values())
            if texto
        )

    @staticmethod
    def valor_texto(valor: Any) -> str:
        if valor is None:
            return ""
        if isinstance(valor, list):
            return " ".join(InstrumentoSearchService.valor_texto(item) for item in valor)
        if isinstance(valor, dict):
            return " ".join(InstrumentoSearchService.valor_texto(item) for item in valor.values())
        return str(valor)

    @staticmethod
    def iso_utc(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @staticmethod
    def index_uid(instrumento_id: uuid.UUID | str) -> str:
        return f"instrumento_{instrumento_id}"

    @staticmethod
    def client() -> httpx.Client:
        return httpx.Client(
            base_url=settings.meili_url,
            headers={"Authorization": f"Bearer {settings.meili_master_key}"},
            timeout=10,
        )

    @staticmethod
    def encode_offset(offset: int) -> str:
        payload = json.dumps({"offset": offset}, separators=(",", ":")).encode("utf-8")
        return urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def decode_offset(cursor: str | None) -> int:
        if not cursor:
            return 0
        padded = cursor + ("=" * (-len(cursor) % 4))
        payload = json.loads(urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
        return max(int(payload.get("offset", 0)), 0)
