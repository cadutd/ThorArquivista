from __future__ import annotations

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ParametroSistema(Base):
    __tablename__ = "parametros_sistema"

    chave: Mapped[str] = mapped_column(String(120), primary_key=True)
    valor: Mapped[dict] = mapped_column(JSONB, nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    atualizado_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
