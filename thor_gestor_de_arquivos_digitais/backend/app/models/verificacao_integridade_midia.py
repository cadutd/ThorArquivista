from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ResultadoVerificacaoIntegridade


class VerificacaoIntegridadeMidia(Base):
    __tablename__ = "verificacoes_integridade_midias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    midia_id: Mapped[int] = mapped_column(ForeignKey("midias_armazenamento.id"), index=True, nullable=False)
    data_inicio: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    data_fim: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usuario_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    resultado: Mapped[ResultadoVerificacaoIntegridade] = mapped_column(
        SAEnum(ResultadoVerificacaoIntegridade, name="resultado_verificacao_integridade"),
        nullable=False,
        index=True,
    )
    software_utilizado: Mapped[str | None] = mapped_column(String(255), nullable=True)
    versao_software: Mapped[str | None] = mapped_column(String(100), nullable=True)
    arquivo_relatorio_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    total_aips_verificados: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_sucesso: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_falha: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    total_alerta: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    relatorio_json: Mapped[dict] = mapped_column(JSONB, default=dict, server_default=text("'{}'::jsonb"), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    evento_id: Mapped[int | None] = mapped_column(ForeignKey("eventos_midia_armazenamento.id"), nullable=True, index=True)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    midia = relationship("MidiaArmazenamento", back_populates="verificacoes_integridade")
    evento = relationship("EventoMidiaArmazenamento")
