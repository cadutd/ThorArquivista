# app/models/midia_armazenamento.py
from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatusMidiaArmazenamento


class TipoMidiaArmazenamento(Base):
    __tablename__ = "tipos_midia_armazenamento"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    tempo_duracao_anos: Mapped[int] = mapped_column(Integer)
    periodicidade_checagem_meses: Mapped[int] = mapped_column(Integer)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    criado_em: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    midias = relationship("MidiaArmazenamento", back_populates="tipo_midia")


class MidiaArmazenamento(Base):
    __tablename__ = "midias_armazenamento"

    id: Mapped[int] = mapped_column(primary_key=True)

    nome: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    tipo_midia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tipos_midia_armazenamento.id", ondelete="RESTRICT"),
        index=True,
    )

    descricao: Mapped[str | None] = mapped_column(String(2000))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    status: Mapped[StatusMidiaArmazenamento] = mapped_column(
        SAEnum(StatusMidiaArmazenamento, name="status_midia_armazenamento"),
        default=StatusMidiaArmazenamento.ATIVA,
        server_default=StatusMidiaArmazenamento.ATIVA.value,
        index=True,
    )
    data_aquisicao: Mapped[Date | None] = mapped_column(Date)
    data_inicio_uso: Mapped[Date | None] = mapped_column(Date)
    data_validade: Mapped[Date | None] = mapped_column(Date, index=True)
    ultima_checagem_integridade: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), index=True)
    proxima_checagem_integridade: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    capacidade_total_bytes: Mapped[int | None] = mapped_column(BigInteger)
    capacidade_utilizada_bytes: Mapped[int | None] = mapped_column(BigInteger)
    identificador_fisico: Mapped[str | None] = mapped_column(String(255))

    midia_origem_id: Mapped[int | None] = mapped_column(
        ForeignKey("midias_armazenamento.id"),
        nullable=True,
        index=True,
    )
    data_desativacao: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    motivo_desativacao: Mapped[str | None] = mapped_column(Text)

    id_posicao_armazenamento: Mapped[int | None] = mapped_column(
        ForeignKey("posicoes_armazenamento.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    tipo_midia = relationship("TipoMidiaArmazenamento", back_populates="midias")
    midia_origem = relationship("MidiaArmazenamento", remote_side=[id])

    copias = relationship(
        "CopiaUnidadeAcondicionamentoDigital",
        back_populates="midia",
    )

    eventos = relationship(
        "EventoMidiaArmazenamento",
    )

    verificacoes_integridade = relationship(
        "VerificacaoIntegridadeMidia",
        back_populates="midia",
    )

    posicao_armazenamento = relationship(
        "PosicaoArmazenamento",
        back_populates="midias",
    )
