from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.models.evento_preservacao import EventoPreservacao
from app.schemas.evento_preservacao import EventoPreservacaoCreate


class EventoPreservacaoService:

    @staticmethod
    def registrar(
        db: Session,
        id_unidade_acondicionamento: int,
        dados: EventoPreservacaoCreate,
    ) -> EventoPreservacao:
        ua = db.get(UnidadeAcondicionamento, id_unidade_acondicionamento)
        if not ua:
            raise LookupError("Unidade de acondicionamento não encontrada.")

        evento = EventoPreservacao(
            id_unidade_acondicionamento=id_unidade_acondicionamento,
            **dados.model_dump(),
        )
        db.add(evento)
        db.commit()
        db.refresh(evento)
        return evento

    @staticmethod
    def listar_por_unidade(
        db: Session,
        id_unidade_acondicionamento: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EventoPreservacao]:
        limit = max(1, min(limit, 500))
        offset = max(0, offset)

        return (
            db.query(EventoPreservacao)
            .filter(
                EventoPreservacao.id_unidade_acondicionamento
                == id_unidade_acondicionamento
            )
            .order_by(EventoPreservacao.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obter_por_id(
        db: Session,
        id_unidade_acondicionamento: int,
        id_evento: int,
    ) -> EventoPreservacao | None:
        return (
            db.query(EventoPreservacao)
            .filter(
                EventoPreservacao.id == id_evento,
                EventoPreservacao.id_unidade_acondicionamento
                == id_unidade_acondicionamento,
            )
            .one_or_none()
        )
