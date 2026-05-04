from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    StatusInstrumentoPesquisa,
    TipoInstrumentoPesquisa,
    VisibilidadeInstrumentoPesquisa,
    TipoCampoInstrumento,
)


class InstrumentoPesquisa(Base):
    __tablename__ = "instrumentos_pesquisa"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tipo: Mapped[TipoInstrumentoPesquisa] = mapped_column(
        SAEnum(TipoInstrumentoPesquisa),
        nullable=False,
        index=True,
    )
    descricao: Mapped[str | None] = mapped_column(Text)
    status: Mapped[StatusInstrumentoPesquisa] = mapped_column(
        SAEnum(StatusInstrumentoPesquisa),
        nullable=False,
        default=StatusInstrumentoPesquisa.RASCUNHO,
        server_default=StatusInstrumentoPesquisa.RASCUNHO.value,
        index=True,
    )
    visibilidade: Mapped[VisibilidadeInstrumentoPesquisa] = mapped_column(
        SAEnum(VisibilidadeInstrumentoPesquisa),
        nullable=False,
        default=VisibilidadeInstrumentoPesquisa.INTERNO,
        server_default=VisibilidadeInstrumentoPesquisa.INTERNO.value,
        index=True,
    )
    responsavel: Mapped[str | None] = mapped_column(String(255))
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    campos = relationship(
        "InstrumentoCampo",
        back_populates="instrumento",
        cascade="all, delete-orphan",
        order_by="InstrumentoCampo.ordem",
    )


class InstrumentoCampo(Base):
    __tablename__ = "instrumento_campos"
    __table_args__ = (
        UniqueConstraint("instrumento_id", "chave", name="uq_instrumento_campos_instrumento_chave"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    instrumento_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("instrumentos_pesquisa.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    chave: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[TipoCampoInstrumento] = mapped_column(
        SAEnum(TipoCampoInstrumento),
        nullable=False,
        index=True,
    )
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    obrigatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    multiplo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    valor_padrao: Mapped[str | None] = mapped_column(Text)
    placeholder: Mapped[str | None] = mapped_column(Text)
    ajuda: Mapped[str | None] = mapped_column(Text)
    aparece_cadastro: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    aparece_listagem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    aparece_busca: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    filtro_avancado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    facetavel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    ordenavel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    opcoes: Mapped[dict | list | None] = mapped_column(JSONB)
    validacoes: Mapped[dict | list | None] = mapped_column(JSONB)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    instrumento = relationship("InstrumentoPesquisa", back_populates="campos")
