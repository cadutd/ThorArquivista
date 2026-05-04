from __future__ import annotations

from enum import StrEnum
import uuid

from app.worker import celery_app


class InstrumentoIndexingEvent(StrEnum):
    REGISTRO_CRIADO = "REGISTRO_CRIADO"
    REGISTRO_ATUALIZADO = "REGISTRO_ATUALIZADO"
    REGISTRO_EXCLUIDO = "REGISTRO_EXCLUIDO"
    REINDEXAR_INSTRUMENTO = "REINDEXAR_INSTRUMENTO"


class InstrumentoIndexingEventPublisher:
    @staticmethod
    def registro_criado(instrumento_id: uuid.UUID | str, registro_id: str) -> None:
        InstrumentoIndexingEventPublisher.publish(
            InstrumentoIndexingEvent.REGISTRO_CRIADO,
            instrumento_id,
            registro_id,
        )

    @staticmethod
    def registro_atualizado(instrumento_id: uuid.UUID | str, registro_id: str) -> None:
        InstrumentoIndexingEventPublisher.publish(
            InstrumentoIndexingEvent.REGISTRO_ATUALIZADO,
            instrumento_id,
            registro_id,
        )

    @staticmethod
    def registro_excluido(instrumento_id: uuid.UUID | str, registro_id: str) -> None:
        InstrumentoIndexingEventPublisher.publish(
            InstrumentoIndexingEvent.REGISTRO_EXCLUIDO,
            instrumento_id,
            registro_id,
        )

    @staticmethod
    def reindexar_instrumento(instrumento_id: uuid.UUID | str) -> None:
        InstrumentoIndexingEventPublisher.publish(
            InstrumentoIndexingEvent.REINDEXAR_INSTRUMENTO,
            instrumento_id,
            None,
        )

    @staticmethod
    def publish(
        event_type: InstrumentoIndexingEvent,
        instrumento_id: uuid.UUID | str,
        registro_id: str | None,
    ) -> None:
        celery_app.send_task(
            "instrumento_indexacao.processar_evento",
            kwargs={
                "event_type": event_type.value,
                "instrumento_id": str(instrumento_id),
                "registro_id": registro_id,
            },
            queue="indexacao",
        )
