"""Durable phase-5 jobs and supplemental audit; domain histories remain canonical."""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AuditoriaGeral(Base):
    __tablename__ = "auditoria_geral"
    __table_args__ = (Index("ix_auditoria_escopo_data", "instrumento_id", text("criado_em DESC"), "id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    agente: Mapped[str] = mapped_column(String(255), nullable=False)
    acao: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entidade: Mapped[str] = mapped_column(String(60), nullable=False)
    entidade_id: Mapped[str | None] = mapped_column(String(255))
    instrumento_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    registro_id: Mapped[str | None] = mapped_column(String(255))
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    operacao_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    detalhe: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Exportacao(Base):
    __tablename__ = "exportacoes"
    __table_args__ = (
        UniqueConstraint("usuario_id", "operacao_id", name="uq_exportacao_operacao"),
        CheckConstraint("status IN ('PENDENTE','PROCESSANDO','CONCLUIDA','FALHOU','CANCELADA','EXPIRADA','DESCARTADA')"),
        CheckConstraint("formato IN ('CSV','JSON','PACOTE')"),
        CheckConstraint("escopo IN ('ADMINISTRATIVO','PUBLICADO')"),
        Index("ix_exportacoes_lease", "status", "lease_ate"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    agente: Mapped[str] = mapped_column(String(255))
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    operacao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    formato: Mapped[str] = mapped_column(String(20))
    escopo: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="PENDENTE", server_default="PENDENTE", index=True)
    revisao: Mapped[int] = mapped_column(Integer)
    schema_json: Mapped[dict] = mapped_column(JSONB)
    parametros: Mapped[dict] = mapped_column(JSONB, default=dict)
    checkpoint: Mapped[str | None] = mapped_column(String(255))
    processados: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    partes: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tentativa: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    lease_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    object_key: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(String(64))
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    erro: Mapped[str | None] = mapped_column(String(255))
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ultimo_descarte_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExportacaoParte(Base):
    __tablename__ = "exportacao_partes"
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    object_key: Mapped[str] = mapped_column(Text)
    checksum: Mapped[str] = mapped_column(String(64))
    quantidade: Mapped[int] = mapped_column(Integer)


class PoliticaRetencao(Base):
    __tablename__ = "politicas_retencao"
    __table_args__ = (
        CheckConstraint("dias >= 1 AND dias <= 36500"),
        CheckConstraint("categoria IN ('LOG_TECNICO','ACESSO_CONSULTIVO','EXPORTACAO','SESSAO','REGISTRO_EXCLUIDO')"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), unique=True)
    categoria: Mapped[str] = mapped_column(String(30), index=True)
    dias: Mapped[int] = mapped_column(Integer)
    instrumento_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    permitir_expurgo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    bloqueada: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ExecucaoRetencao(Base):
    __tablename__ = "execucoes_retencao"
    __table_args__ = (CheckConstraint("status IN ('PENDENTE','PROCESSANDO','CONCLUIDA','FALHOU','CANCELADA')"),
                     UniqueConstraint("usuario_id", "operacao_id", name="uq_retencao_operacao"),
                     Index("ix_retencao_lease", "status", "lease_ate"))
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    politica_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    agente: Mapped[str] = mapped_column(String(255))
    operacao_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    simulacao: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDENTE", index=True)
    checkpoint: Mapped[str | None] = mapped_column(String(255))
    processados: Mapped[int] = mapped_column(Integer, default=0)
    elegiveis: Mapped[int] = mapped_column(Integer, default=0)
    bloqueados: Mapped[int] = mapped_column(Integer, default=0)
    removidos: Mapped[int] = mapped_column(Integer, default=0)
    lease_token: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lease_ate: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    erro: Mapped[str | None] = mapped_column(String(255))
    corte_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LogRequisicao(Base):
    __tablename__ = "logs_requisicoes"
    __table_args__ = (Index("ix_logs_retencao_lote", "categoria", "criado_em", "id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str] = mapped_column(String(64), index=True)
    categoria: Mapped[str] = mapped_column(String(30), index=True)
    metodo: Mapped[str] = mapped_column(String(10))
    rota: Mapped[str] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(Integer)
    duracao_ms: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
