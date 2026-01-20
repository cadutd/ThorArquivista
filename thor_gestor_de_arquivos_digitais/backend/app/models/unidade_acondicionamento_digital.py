# app/models/unidade_acondicionamento_digital.py
from __future__ import annotations

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UnidadeAcondicionamentoDigital(Base):
    __tablename__ = "unidades_acondicionamento_digitais"

    id_unidade_acondicionamento: Mapped[int] = mapped_column(
        ForeignKey("unidades_acondicionamento.id"),
        primary_key=True,
    )

    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    status_fixidez: Mapped[str | None] = mapped_column(nullable=True)

    unidade = relationship(
        "UnidadeAcondicionamento",
        back_populates="digital",
        uselist=False,
    )
