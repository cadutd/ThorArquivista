from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import TipoEntidadeProdutora


class EntidadeProdutora(Base):
    __tablename__ = "entidades_produtoras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    nome_normalizado: Mapped[str | None] = mapped_column(String(255), index=True)
    sigla: Mapped[str | None] = mapped_column(String(50), index=True)
    codigo_referencia: Mapped[str | None] = mapped_column(String(100), index=True)
    tipo_entidade: Mapped[TipoEntidadeProdutora] = mapped_column(
        SAEnum(TipoEntidadeProdutora),
        nullable=False,
        index=True,
    )
    natureza_juridica: Mapped[str | None] = mapped_column(String(100))
    data_inicio: Mapped[Date | None] = mapped_column(Date)
    data_fim: Mapped[Date | None] = mapped_column(Date)
    entidade_ativa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
    historico: Mapped[str | None] = mapped_column(Text)
    competencias_funcoes: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(50))
    site: Mapped[str | None] = mapped_column(String(255))
    endereco_logradouro: Mapped[str | None] = mapped_column(String(255))
    endereco_numero: Mapped[str | None] = mapped_column(String(50))
    endereco_complemento: Mapped[str | None] = mapped_column(String(100))
    endereco_bairro: Mapped[str | None] = mapped_column(String(100))
    endereco_municipio: Mapped[str | None] = mapped_column(String(100))
    endereco_uf: Mapped[str | None] = mapped_column(String(2))
    endereco_cep: Mapped[str | None] = mapped_column(String(20))
    endereco_pais: Mapped[str | None] = mapped_column(
        String(100),
        default="Brasil",
        server_default="Brasil",
    )
    id_entidade_superior: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("entidades_produtoras.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    entidade_superior = relationship(
        "EntidadeProdutora",
        remote_side=[id],
        foreign_keys=[id_entidade_superior],
        backref="entidades_subordinadas",
    )
