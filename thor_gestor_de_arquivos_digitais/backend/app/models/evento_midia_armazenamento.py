from __future__ import annotations

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ResultadoEventoPreservacao, TipoEventoPreservacao


class EventoMidiaArmazenamento(Base):
    __tablename__ = "eventos_midia_armazenamento"

    id: Mapped[int] = mapped_column(primary_key=True)

    id_midia_armazenamento: Mapped[int] = mapped_column(
        ForeignKey("midias_armazenamento.id"),
        index=True,
        nullable=False,
    )

    tipo_evento: Mapped[TipoEventoPreservacao] = mapped_column(
        SAEnum(TipoEventoPreservacao, name="tipo_evento_preservacao"),
        index=True,
        nullable=False,
    )

    resultado: Mapped[ResultadoEventoPreservacao] = mapped_column(
        SAEnum(ResultadoEventoPreservacao, name="resultado_evento_preservacao"),
        default=ResultadoEventoPreservacao.SUCESSO,
        index=True,
        nullable=False,
    )

    detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)

    agente: Mapped[str | None] = mapped_column(String(255), nullable=True)

    correlacao: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
