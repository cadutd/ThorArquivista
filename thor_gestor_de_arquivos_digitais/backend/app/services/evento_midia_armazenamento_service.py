from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.evento_midia_armazenamento import EventoMidiaArmazenamento
from app.models.midia_armazenamento import MidiaArmazenamento
from app.schemas.evento_midia_armazenamento import EventoMidiaArmazenamentoCreate


class EventoMidiaArmazenamentoService:
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

        evento = EventoMidiaArmazenamento(
            id_midia_armazenamento=id_midia_armazenamento,
            **dados.model_dump(),
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
