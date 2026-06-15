from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatusMigracaoMidia


class MigracaoMidia(Base):
    __tablename__ = "migracoes_midias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    midia_origem_id: Mapped[int] = mapped_column(ForeignKey("midias_armazenamento.id"), index=True)
    midia_destino_id: Mapped[int] = mapped_column(ForeignKey("midias_armazenamento.id"), index=True)
    data_inicio: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    data_conclusao: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    usuario_responsavel_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[StatusMigracaoMidia] = mapped_column(
        SAEnum(StatusMigracaoMidia, name="status_migracao_midia"),
        default=StatusMigracaoMidia.EM_EXECUCAO,
        server_default=StatusMigracaoMidia.EM_EXECUCAO.value,
        index=True,
    )
    motivo_migracao: Mapped[str] = mapped_column(Text)
    procedimento_utilizado: Mapped[str] = mapped_column(Text)
    software_utilizado: Mapped[str | None] = mapped_column(Text)
    versao_software: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    relatorio_integridade_origem: Mapped[str | None] = mapped_column(Text)
    relatorio_integridade_destino: Mapped[str | None] = mapped_column(Text)
    evento_id: Mapped[int | None] = mapped_column(ForeignKey("eventos_midia_armazenamento.id"), nullable=True)
    etapas: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    relatorios: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    midia_origem = relationship("MidiaArmazenamento", foreign_keys=[midia_origem_id])
    midia_destino = relationship("MidiaArmazenamento", foreign_keys=[midia_destino_id])
