from __future__ import annotations

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TipoEventoPreservacao, ResultadoEventoPreservacao


class EventoPreservacao(Base):
    __tablename__ = "eventos_preservacao"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Sempre ocorre sobre uma Unidade de Acondicionamento
    id_unidade_acondicionamento: Mapped[int] = mapped_column(
        ForeignKey("unidades_acondicionamento.id"),
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
