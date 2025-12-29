from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.schemas.unidade_acondicionamento import (
    UnidadeAcondicionamentoCreate,
)


class UnidadeAcondicionamentoService:

    @staticmethod
    def criar(
        db: Session,
        dados: UnidadeAcondicionamentoCreate,
    ) -> UnidadeAcondicionamento:
        ua = UnidadeAcondicionamento(**dados.model_dump())
        db.add(ua)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Já existe uma unidade de acondicionamento com o mesmo identificador."
            )
        db.refresh(ua)
        return ua

    @staticmethod
    def listar(
        db: Session,
        limit: int = 50,
        offset: int = 0,
    ) -> list[UnidadeAcondicionamento]:
        return (
            db.query(UnidadeAcondicionamento)
            .order_by(UnidadeAcondicionamento.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def obter_por_id(
        db: Session,
        id: int,
    ) -> UnidadeAcondicionamento | None:
        return db.get(UnidadeAcondicionamento, id)
