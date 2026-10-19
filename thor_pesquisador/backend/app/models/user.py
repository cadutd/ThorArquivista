from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    govbr_sub: Mapped[str | None] = mapped_column(String(64), unique=True)
    cpf: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False,
                                        default=lambda: "usuario_" + uuid.uuid4().hex)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    observacoes: Mapped[str | None] = mapped_column(Text)
    excluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sessoes = relationship("Sessao", back_populates="usuario", cascade="all, delete-orphan")


class Sessao(Base):
    __tablename__ = "sessoes"
    __table_args__ = (CheckConstraint("usuario_id IS NOT NULL OR cpf_consultivo IS NOT NULL", name="ck_sessao_identidade"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"))
    cpf_consultivo: Mapped[str | None] = mapped_column(String(11))
    nome_consultivo: Mapped[str | None] = mapped_column(String(255))
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", back_populates="sessoes")
