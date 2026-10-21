import uuid
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ImportacaoRegistros(Base):
    __tablename__ = "importacoes_registros"
    __table_args__ = (CheckConstraint("status IN ('EM_ANDAMENTO','INTERROMPIDA','CONCLUIDA')",
                                     name="ck_importacao_status"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="RESTRICT"), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    assinatura: Mapped[str] = mapped_column(String(64))
    configuracao: Mapped[dict] = mapped_column(JSONB)
    schema_version: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    processados: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="EM_ANDAMENTO")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
