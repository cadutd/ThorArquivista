from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Papel(Base):
    __tablename__ = "papeis"
    nome: Mapped[str] = mapped_column(String(40), primary_key=True)
    permissoes: Mapped[list] = mapped_column(JSONB, nullable=False)
    titulo: Mapped[str | None] = mapped_column(String(150))
    descricao: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")


class AcessoInstrumento(Base):
    __tablename__ = "acessos_instrumento"
    __table_args__ = (
        Index("uq_acesso_escopo", "usuario_id", "papel", "instrumento_id", unique=True,
              postgresql_where=text("instrumento_id IS NOT NULL")),
        Index("uq_acesso_global", "usuario_id", "papel", unique=True,
              postgresql_where=text("instrumento_id IS NULL")),
        CheckConstraint("origem IN ('MANUAL', 'USUARIO')",
                        name="ck_acesso_origem"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    papel: Mapped[str] = mapped_column(String(40), ForeignKey("papeis.nome"))
    origem: Mapped[str] = mapped_column(String(10), nullable=False, default="MANUAL", server_default="MANUAL")
    instrumento_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="CASCADE"), index=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EditorialRegistro(Base):
    __tablename__ = "editorial_registros"
    __table_args__ = (UniqueConstraint("instrumento_id", "registro_id", name="uq_editorial_registro"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="RESTRICT"), index=True)
    registro_id: Mapped[str] = mapped_column(String(255))
    status_editorial: Mapped[str] = mapped_column(String(40), default="RASCUNHO", server_default="RASCUNHO", index=True)
    status_operacional: Mapped[str] = mapped_column(String(40), default="ATIVO")
    versao: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    versao_publicada: Mapped[int | None] = mapped_column(Integer)
    snapshot_id: Mapped[str | None] = mapped_column(String(255))
    aprovacao_hash: Mapped[str | None] = mapped_column(String(64))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PublicacaoInstrumento(Base):
    __tablename__ = "publicacoes_instrumento"
    __table_args__ = (UniqueConstraint("instrumento_id", "versao", name="uq_publicacao_instrumento"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="RESTRICT"), index=True)
    versao: Mapped[int] = mapped_column(Integer)
    schema_json: Mapped[dict] = mapped_column(JSONB)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="RESTRICT"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventoEditorial(Base):
    __tablename__ = "eventos_editoriais"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    registro_id: Mapped[str | None] = mapped_column(String(255))
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    agente: Mapped[str] = mapped_column(String(255))
    acao: Mapped[str] = mapped_column(String(40))
    estado_anterior: Mapped[str] = mapped_column(String(40))
    estado_novo: Mapped[str] = mapped_column(String(40))
    versao: Mapped[int] = mapped_column(Integer)
    justificativa: Mapped[str | None] = mapped_column(String(4000))
    resultado: Mapped[dict] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class PublicacaoImagem(Base):
    __tablename__ = "publicacao_imagens"
    snapshot_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    referencia: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    imagem_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("imagens_documento.id", ondelete="RESTRICT"), primary_key=True, index=True)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="RESTRICT"), index=True)
