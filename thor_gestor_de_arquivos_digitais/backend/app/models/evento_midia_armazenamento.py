from __future__ import annotations

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ResultadoEventoPreservacao, TipoEventoMidiaArmazenamento


class EventoMidiaArmazenamento(Base):
    __tablename__ = "eventos_midia_armazenamento"

    id: Mapped[int] = mapped_column(primary_key=True)

    id_midia_armazenamento: Mapped[int] = mapped_column(
        ForeignKey("midias_armazenamento.id"),
        index=True,
        nullable=False,
    )

    tipo_evento: Mapped[TipoEventoMidiaArmazenamento] = mapped_column(
        SAEnum(TipoEventoMidiaArmazenamento, name="tipo_evento_midia_armazenamento"),
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

    data_evento: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )

    premis_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    evento_relacionado_id: Mapped[int | None] = mapped_column(
        ForeignKey("eventos_midia_armazenamento.id"),
        nullable=True,
        index=True,
    )

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
