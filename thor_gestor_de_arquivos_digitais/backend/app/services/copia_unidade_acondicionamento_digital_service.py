from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.enums import TipoSuporte
from app.models.unidade_acondicionamento import UnidadeAcondicionamento
from app.models.copia_unidade_acondicionamento_digital import (
    CopiaUnidadeAcondicionamentoDigital,
)
from app.schemas.copia_unidade_acondicionamento_digital import (
    CopiaUnidadeAcondicionamentoDigitalCreate,
)


class CopiaUnidadeAcondicionamentoDigitalService:

    @staticmethod
    def criar(
        db: Session,
        id_unidade_acondicionamento: int,
        dados: CopiaUnidadeAcondicionamentoDigitalCreate,
    ) -> CopiaUnidadeAcondicionamentoDigital:

        ua = db.get(UnidadeAcondicionamento, id_unidade_acondicionamento)
        if not ua:
            raise LookupError("Unidade de acondicionamento não encontrada.")

        if ua.tipo_suporte != TipoSuporte.DIGITAL:
            raise ValueError(
                "Somente unidades de acondicionamento digitais podem possuir cópias digitais."
            )

        payload = dados.model_dump()
        payload["id_unidade_acondicionamento"] = id_unidade_acondicionamento

        copia = CopiaUnidadeAcondicionamentoDigital(**payload)
        db.add(copia)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ValueError(
                "Já existe uma cópia cadastrada para essa unidade, mídia e URI."
            )

        db.refresh(copia)
        return copia

    @staticmethod
    def listar_por_unidade(
        db: Session,
        id_unidade_acondicionamento: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CopiaUnidadeAcondicionamentoDigital]:

        return (
            db.query(CopiaUnidadeAcondicionamentoDigital)
            .filter(
                CopiaUnidadeAcondicionamentoDigital.id_unidade_acondicionamento
                == id_unidade_acondicionamento
            )
            .order_by(CopiaUnidadeAcondicionamentoDigital.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
