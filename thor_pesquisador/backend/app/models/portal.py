import uuid
from datetime import date, datetime
from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ConfiguracaoPortal(Base):
    __tablename__ = "configuracao_portal"
    __table_args__ = (CheckConstraint("id = 1", name="ck_portal_singleton"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    nome_instituicao: Mapped[str] = mapped_column(String(150), nullable=False)
    cores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    versao: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class AcessoPortal(Base):
    __tablename__ = "portal_acessos"
    sessao_chave: Mapped[str] = mapped_column(String(64), primary_key=True)
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="CASCADE"), primary_key=True)
    dia: Mapped[date] = mapped_column(Date, primary_key=True)
    __table_args__ = (Index("ix_portal_acessos_dia_instrumento", "dia", "instrumento_id"),)



class ContagemPortal(Base):
    __tablename__ = "portal_contagens"
    instrumento_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instrumentos.id", ondelete="CASCADE"), primary_key=True)
    dia: Mapped[date] = mapped_column(Date, primary_key=True, index=True)
    quantidade: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
