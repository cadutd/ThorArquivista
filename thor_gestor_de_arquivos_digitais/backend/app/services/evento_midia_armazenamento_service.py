from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.evento_midia_armazenamento import EventoMidiaArmazenamento
from app.models.midia_armazenamento import MidiaArmazenamento
from app.models.enums import ResultadoEventoPreservacao, TipoEventoMidiaArmazenamento
from app.schemas.evento_midia_armazenamento import EventoMidiaArmazenamentoCreate


class EventoMidiaArmazenamentoService:
    @staticmethod
    def montar_premis_json(
        *,
        midia_id: int,
        tipo_evento: TipoEventoMidiaArmazenamento,
        resultado: ResultadoEventoPreservacao,
        data_evento: datetime,
        detalhe: str | None = None,
        agente: str | None = None,
    ) -> dict[str, Any]:
        data_utc = data_evento.astimezone(timezone.utc) if data_evento.tzinfo else data_evento.replace(tzinfo=timezone.utc)
        return {
            "eventType": tipo_evento.value,
            "eventDateTime": data_utc.isoformat(),
            "eventDetail": detalhe,
            "eventOutcomeInformation": {
                "eventOutcome": resultado.value,
                "eventOutcomeDetail": detalhe or resultado.value,
            },
            "linkingAgentIdentifier": {
                "linkingAgentIdentifierType": "usuario",
                "linkingAgentIdentifierValue": agente,
            },
            "linkingObjectIdentifier": {
                "linkingObjectIdentifierType": "midia_armazenamento",
                "linkingObjectIdentifierValue": str(midia_id),
            },
        }

    @staticmethod
    def registrar(
        db: Session,
        id_midia_armazenamento: int,
        dados: EventoMidiaArmazenamentoCreate,
        *,
        commit: bool = True,
    ) -> EventoMidiaArmazenamento:
        midia = db.get(MidiaArmazenamento, id_midia_armazenamento)
        if not midia:
            raise LookupError("Midia de armazenamento nao encontrada.")

        payload = dados.model_dump()
        data_evento = payload.get("data_evento") or datetime.now(timezone.utc)
        payload["data_evento"] = data_evento
        payload["premis_json"] = payload.get("premis_json") or EventoMidiaArmazenamentoService.montar_premis_json(
            midia_id=id_midia_armazenamento,
            tipo_evento=payload["tipo_evento"],
            resultado=payload["resultado"],
            data_evento=data_evento,
            detalhe=payload.get("detalhe"),
            agente=payload.get("agente"),
        )

        evento = EventoMidiaArmazenamento(
            id_midia_armazenamento=id_midia_armazenamento,
            **payload,
        )
        db.add(evento)
        if commit:
            db.commit()
            db.refresh(evento)
        return evento

    @staticmethod
    def listar_por_midia(
        db: Session,
        id_midia_armazenamento: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EventoMidiaArmazenamento]:
        midia = db.get(MidiaArmazenamento, id_midia_armazenamento)
        if not midia:
            raise LookupError("Midia de armazenamento nao encontrada.")

        limit = max(1, min(limit, 500))
        offset = max(0, offset)

        return (
            db.query(EventoMidiaArmazenamento)
            .filter(
                EventoMidiaArmazenamento.id_midia_armazenamento
                == id_midia_armazenamento
            )
            .order_by(EventoMidiaArmazenamento.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obter_por_id(
        db: Session,
        id_midia_armazenamento: int,
        id_evento: int,
    ) -> EventoMidiaArmazenamento | None:
        return (
            db.query(EventoMidiaArmazenamento)
            .filter(
                EventoMidiaArmazenamento.id == id_evento,
                EventoMidiaArmazenamento.id_midia_armazenamento
                == id_midia_armazenamento,
            )
            .one_or_none()
        )
