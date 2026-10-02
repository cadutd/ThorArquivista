from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Instrumento(Base):
    __tablename__ = "instrumentos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="RASCUNHO", server_default="RASCUNHO")
    visibilidade: Mapped[str] = mapped_column(String(40), nullable=False, default="INTERNO", server_default="INTERNO")
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    campos = relationship("InstrumentoCampo", back_populates="instrumento", cascade="all, delete-orphan", order_by="InstrumentoCampo.ordem")


class InstrumentoCampo(Base):
    __tablename__ = "instrumento_campos"
    __table_args__ = (UniqueConstraint("instrumento_id", "chave", name="uq_instrumento_campos_chave"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="CASCADE"), nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    chave: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    obrigatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    multiplo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    opcoes: Mapped[dict | list | None] = mapped_column(JSONB)
    validacoes: Mapped[dict | list | None] = mapped_column(JSONB)
    aparece_cadastro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    aparece_listagem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    aparece_busca: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    instrumento = relationship("Instrumento", back_populates="campos")
