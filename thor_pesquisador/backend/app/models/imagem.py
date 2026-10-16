from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImagemDocumento(Base):
    __tablename__ = "imagens_documento"
    __table_args__ = (
        CheckConstraint("tipo_referencia IN ('UPLOAD','URL','IIIF','REPOSITORIO_EXTERNO')"),
        CheckConstraint("direitos_acesso IN ('PUBLICO','INTERNO','RESTRITO')"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo_referencia: Mapped[str] = mapped_column(String(40), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str | None] = mapped_column(String(255), unique=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String(255))
    thumbnail_uri: Mapped[str | None] = mapped_column(Text)
    manifest_iiif_uri: Mapped[str | None] = mapped_column(Text)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    largura: Mapped[int | None] = mapped_column(Integer)
    altura: Mapped[int | None] = mapped_column(Integer)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64))
    direitos_acesso: Mapped[str] = mapped_column(String(40), nullable=False, default="INTERNO", index=True)
    metadados_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    criado_por: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class RegistroImagem(Base):
    __tablename__ = "registro_imagens"
    __table_args__ = (
        CheckConstraint("ordem >= 0"),
        Index("ix_registro_imagens_registro", "instrumento_id", "registro_id", "ordem"),
        Index("uq_registro_imagens_principal", "instrumento_id", "registro_id", unique=True, postgresql_where=text("principal")),
    )

    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="CASCADE"), primary_key=True)
    registro_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    imagem_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("imagens_documento.id", ondelete="RESTRICT"), primary_key=True, index=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    legenda: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AuditoriaImagem(Base):
    __tablename__ = "auditoria_imagens"
    __table_args__ = (Index("ix_imagens_auditoria_escopo_data", "instrumento_id", text("criado_em DESC"), "id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)
    agente: Mapped[str | None] = mapped_column(String(255))
    # Identifiers are retained even after the referenced entity is deleted.
    imagem_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    instrumento_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    registro_id: Mapped[str | None] = mapped_column(String(255))
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    acao: Mapped[str] = mapped_column(String(60), nullable=False)
    detalhe: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
