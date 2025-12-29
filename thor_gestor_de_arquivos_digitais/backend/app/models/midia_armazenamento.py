# app/models/midia_armazenamento.py
from __future__ import annotations

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoMidiaArmazenamento


class MidiaArmazenamento(Base):
    __tablename__ = "midias_armazenamento"

    id: Mapped[int] = mapped_column(primary_key=True)

    nome: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    tipo: Mapped[TipoMidiaArmazenamento] = mapped_column(
        SAEnum(TipoMidiaArmazenamento), index=True
    )

    descricao: Mapped[str | None] = mapped_column(String(2000))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    copias = relationship(
        "CopiaUnidadeAcondicionamentoDigital",
        back_populates="midia",
    )
