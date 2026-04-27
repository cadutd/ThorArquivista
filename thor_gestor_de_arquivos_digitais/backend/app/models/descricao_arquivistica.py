from __future__ import annotations

import uuid

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RegistroDescritivo(Base):
    __tablename__ = "registros_descritivos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("registros_descritivos.id", ondelete="CASCADE"),
        index=True,
    )
    nivel: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    norma: Mapped[str] = mapped_column(String(20), nullable=False, default="NOBRADE")
    codigo_referencia: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    data_inicial: Mapped[Date | None] = mapped_column(Date)
    data_final: Mapped[Date | None] = mapped_column(Date)
    dimensao: Mapped[str | None] = mapped_column(String(255))
    suporte: Mapped[str | None] = mapped_column(String(255))
    produtor: Mapped[str | None] = mapped_column(String(500))
    historia_administrativa: Mapped[str | None] = mapped_column(Text)
    historia_arquivistica: Mapped[str | None] = mapped_column(Text)
    procedencia: Mapped[str | None] = mapped_column(Text)
    ambito_conteudo: Mapped[str | None] = mapped_column(Text)
    avaliacao_eliminacao: Mapped[str | None] = mapped_column(Text)
    incorporacoes: Mapped[str | None] = mapped_column(Text)
    sistema_arranjo: Mapped[str | None] = mapped_column(Text)
    condicoes_acesso: Mapped[str | None] = mapped_column(Text)
    condicoes_reproducao: Mapped[str | None] = mapped_column(Text)
    idioma: Mapped[str | None] = mapped_column(String(255))
    caracteristicas_tecnicas: Mapped[str | None] = mapped_column(Text)
    originais: Mapped[str | None] = mapped_column(Text)
    copias: Mapped[str | None] = mapped_column(Text)
    unidades_relacionadas: Mapped[str | None] = mapped_column(Text)
    publicacoes: Mapped[str | None] = mapped_column(Text)
    notas: Mapped[str | None] = mapped_column(Text)
    arquivista_responsavel: Mapped[str | None] = mapped_column(String(255))
    regras_convencoes: Mapped[str | None] = mapped_column(Text)
    data_descricao: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    assuntos: Mapped[str | None] = mapped_column(Text)
    pessoas: Mapped[str | None] = mapped_column(Text)
    locais: Mapped[str | None] = mapped_column(Text)
    entidades: Mapped[str | None] = mapped_column(Text)
    eventos: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship(
        "RegistroDescritivo",
        remote_side=[id],
        back_populates="children",
    )
    children = relationship(
        "RegistroDescritivo",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
