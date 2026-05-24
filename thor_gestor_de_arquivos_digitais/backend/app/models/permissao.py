from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


perfil_permissao = Table(
    "perfil_permissao",
    Base.metadata,
    Column("perfil_id", UUID(as_uuid=True), ForeignKey("perfis.id", ondelete="CASCADE"), primary_key=True),
    Column("permissao_id", UUID(as_uuid=True), ForeignKey("permissoes.id", ondelete="CASCADE"), primary_key=True),
)


class Permissao(Base):
    __tablename__ = "permissoes"
    __table_args__ = (
        UniqueConstraint("funcao", "acao", name="uq_permissoes_funcao_acao"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    modulo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    funcao: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    acao: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    perfis: Mapped[list[Perfil]] = relationship(
        "Perfil",
        secondary=perfil_permissao,
        back_populates="permissoes",
    )


class Perfil(Base):
    __tablename__ = "perfis"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true", index=True)
    sistema: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    permissoes: Mapped[list[Permissao]] = relationship(
        "Permissao",
        secondary=perfil_permissao,
        back_populates="perfis",
    )
