from __future__ import annotations

from datetime import UTC, datetime
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
