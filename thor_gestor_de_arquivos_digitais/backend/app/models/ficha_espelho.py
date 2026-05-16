from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModeloFichaEspelho(Base):
    __tablename__ = "modelos_ficha_espelho"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    campos: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    tamanho_papel: Mapped[str] = mapped_column(String(20), default="A4", nullable=False)
    orientacao: Mapped[str] = mapped_column(String(20), default="RETRATO", nullable=False)
    colunas: Mapped[int] = mapped_column(default=1, nullable=False)
    largura_cm: Mapped[float] = mapped_column(Float, default=21.0, nullable=False)
    altura_cm: Mapped[float] = mapped_column(Float, default=29.7, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
