from __future__ import annotations

import uuid

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import EsferaAdministrativa


class InstituicaoArquivo(Base):
    __tablename__ = "instituicao_arquivo"
    __table_args__ = (
        UniqueConstraint("singleton_key", name="uq_instituicao_arquivo_singleton"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    singleton_key: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sigla: Mapped[str | None] = mapped_column(String(50))
    codigo_referencia: Mapped[str | None] = mapped_column(String(100))
    natureza_juridica: Mapped[str | None] = mapped_column(String(100))
    esfera_administrativa: Mapped[EsferaAdministrativa | None] = mapped_column(
        SAEnum(EsferaAdministrativa),
        nullable=True,
    )
    cnpj: Mapped[str | None] = mapped_column(String(20))
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
    responsavel_nome: Mapped[str | None] = mapped_column(String(255))
    responsavel_cargo: Mapped[str | None] = mapped_column(String(255))
    responsavel_email: Mapped[str | None] = mapped_column(String(255))
    responsavel_telefone: Mapped[str | None] = mapped_column(String(50))
    historico: Mapped[str | None] = mapped_column(Text)
    missao: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criada_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    atualizada_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
