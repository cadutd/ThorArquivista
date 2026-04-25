# app/models/copia_unidade_acondicionamento_digital.py
from __future__ import annotations

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FuncaoCopia, StatusCopia


class CopiaUnidadeAcondicionamentoDigital(Base):
    __tablename__ = "copias_unidades_acondicionamento_digitais"

    __table_args__ = (
        UniqueConstraint(
            "id_unidade_acondicionamento",
            "id_midia_armazenamento",
            "uri_copia",
            name="uq_copia_unidade_acondicionamento_midia_uri",
        ),
        Index(
            "ix_copia_unidade_acondicionamento_funcao",
            "id_unidade_acondicionamento",
            "funcao_copia",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    id_unidade_acondicionamento: Mapped[int] = mapped_column(
        ForeignKey("unidades_acondicionamento.id"),
        index=True,
    )

    id_midia_armazenamento: Mapped[int] = mapped_column(
        ForeignKey("midias_armazenamento.id"),
        index=True,
    )

    uri_copia: Mapped[str] = mapped_column(String(1200))

    funcao_copia: Mapped[FuncaoCopia] = mapped_column(
        SAEnum(FuncaoCopia), index=True
    )

    status_copia: Mapped[StatusCopia] = mapped_column(
        SAEnum(StatusCopia),
        default=StatusCopia.ATIVA,
        index=True,
    )

    algoritmo_fixidez: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )

    hash_fixidez: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )

    ultima_verificacao_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    id_posicao_armazenamento: Mapped[int | None] = mapped_column(
        ForeignKey("posicoes_armazenamento.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    criada_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # --------------------
    # Relacionamentos
    # --------------------

    midia = relationship(
        "MidiaArmazenamento",
        back_populates="copias",
    )

    unidade = relationship(
        "UnidadeAcondicionamento",
        back_populates="copias_digitais",
    )

    posicao_armazenamento = relationship(
        "PosicaoArmazenamento",
        back_populates="copias",
    )
