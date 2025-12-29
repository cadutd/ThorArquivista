from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.midia_armazenamento import MidiaArmazenamento
from app.schemas.midia_armazenamento import MidiaArmazenamentoCreate


class MidiaArmazenamentoService:

    @staticmethod
    def criar(
        db: Session,
        dados: MidiaArmazenamentoCreate,
    ) -> MidiaArmazenamento:
        midia = MidiaArmazenamento(**dados.model_dump())
        db.add(midia)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Já existe uma mídia de armazenamento com o mesmo nome."
            )
        db.refresh(midia)
        return midia

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MidiaArmazenamento]:
        return (
            db.query(MidiaArmazenamento)
            .order_by(MidiaArmazenamento.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
