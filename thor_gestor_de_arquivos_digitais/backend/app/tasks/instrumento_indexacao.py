from __future__ import annotations

from typing import Any

from app.db.mongo import get_instrumento_registros_collection
from app.services.instrumento_indexing_events import InstrumentoIndexingEvent
from app.services.instrumento_search_service import InstrumentoSearchService
from app.worker import celery_app


@celery_app.task(
    name="instrumento_indexacao.processar_evento",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def processar_evento(
    event_type: str,
    instrumento_id: str,
    registro_id: str | None = None,
) -> dict[str, Any]:
    event = InstrumentoIndexingEvent(event_type)

    if event == InstrumentoIndexingEvent.REINDEXAR_INSTRUMENTO:
        return reindexar_instrumento(instrumento_id)

    if registro_id is None:
        raise ValueError("registro_id e obrigatorio para eventos de registro.")

    if event == InstrumentoIndexingEvent.REGISTRO_EXCLUIDO:
        InstrumentoSearchService.remover_registro(instrumento_id, registro_id)
        return {"event_type": event.value, "instrumento_id": instrumento_id, "registro_id": registro_id}

    documento = get_instrumento_registros_collection().find_one(
        {
            "_id": registro_id,
            "instrumento_id": instrumento_id,
        }
    )
    if not documento:
        InstrumentoSearchService.remover_registro(instrumento_id, registro_id)
        return {
            "event_type": event.value,
            "instrumento_id": instrumento_id,
            "registro_id": registro_id,
            "indexed": False,
        }

    if documento.get("status") == "EXCLUIDO":
        InstrumentoSearchService.remover_registro(instrumento_id, registro_id)
        indexed = False
    else:
        InstrumentoSearchService.indexar_registro(documento)
        indexed = True

    return {
        "event_type": event.value,
        "instrumento_id": instrumento_id,
        "registro_id": registro_id,
        "indexed": indexed,
    }


def reindexar_instrumento(instrumento_id: str) -> dict[str, Any]:
    collection = get_instrumento_registros_collection()
    count = 0

    for documento in collection.find({"instrumento_id": instrumento_id}):
        if documento.get("status") == "EXCLUIDO":
            InstrumentoSearchService.remover_registro(instrumento_id, documento["_id"])
        else:
            InstrumentoSearchService.indexar_registro(documento)
            count += 1

    return {
        "event_type": InstrumentoIndexingEvent.REINDEXAR_INSTRUMENTO.value,
        "instrumento_id": instrumento_id,
        "indexed": count,
    }
