import uuid
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

ESTADOS = ("RECEBENDO", "ANALISANDO", "AGUARDANDO_MAPA", "VALIDANDO", "AGUARDANDO_CONFIRMACAO",
           "ERROS_VALIDACAO", "PENDENTE", "IMPORTANDO", "CONCLUIDA", "FALHOU", "PAUSADA", "CANCELADA", "EXPIRADA")


class ImportacaoAsync(Base):
    __tablename__ = "importacoes_assincronas"
    __table_args__ = (
        CheckConstraint("status IN (" + ",".join("'" + state + "'" for state in ESTADOS) + ")", name="ck_importacao_async_status"),
        Index("ix_importacao_async_lease", "status", "lease_ate"),
        Index("ix_importacao_async_usuario_data", "usuario_id", "instrumento_id", "criado_em"),
        Index("ix_importacao_async_expira", "expira_em", "limpo_em"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="RESTRICT"), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"), index=True)
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    formato: Mapped[str] = mapped_column(String(12))
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger)
    bytes_recebidos: Mapped[int] = mapped_column(BigInteger, default=0)
    checksum: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="RECEBENDO")
    phase: Mapped[str] = mapped_column(String(32), default="ANALISANDO")
    total: Mapped[int] = mapped_column(Integer, default=0)
    processados: Mapped[int] = mapped_column(Integer, default=0)
    fase_processados: Mapped[int] = mapped_column(Integer, default=0)
    validos: Mapped[int] = mapped_column(Integer, default=0)
    invalidos: Mapped[int] = mapped_column(Integer, default=0)
    schema_version: Mapped[int] = mapped_column(Integer)
    schema_json: Mapped[list] = mapped_column(JSONB, default=list)
    analise: Mapped[dict] = mapped_column(JSONB, default=dict)
    configuracao: Mapped[dict] = mapped_column(JSONB, default=dict)
    relatorio: Mapped[dict] = mapped_column(JSONB, default=dict)
    geracao: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erro: Mapped[str | None] = mapped_column(String(255))
    inicio_fase: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    limpo_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ImportacaoAsyncParte(Base):
    __tablename__ = "importacoes_assincronas_partes"
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("importacoes_assincronas.id", ondelete="RESTRICT"), primary_key=True)
    categoria: Mapped[str] = mapped_column(String(12), primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    object_key: Mapped[str] = mapped_column(String(255))
    checksum: Mapped[str] = mapped_column(String(64))
    tamanho_bytes: Mapped[int] = mapped_column(BigInteger)
    quantidade: Mapped[int] = mapped_column(Integer, default=0)
    linhas: Mapped[int] = mapped_column(Integer, default=0)
    aplicada: Mapped[bool] = mapped_column(Boolean, default=False)
    erros_key: Mapped[str | None] = mapped_column(String(255))
    erros_checksum: Mapped[str | None] = mapped_column(String(64))
