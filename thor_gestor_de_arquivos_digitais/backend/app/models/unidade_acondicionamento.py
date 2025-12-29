# app/models/unidade_acondicionamento.py
from __future__ import annotations

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base
from app.models.enums import (
    TipoSuporte,
    TipoUnidade,
    NivelAcesso,
    StatusUnidade,
)


class UnidadeAcondicionamento(Base):
    __tablename__ = "unidades_acondicionamento"

    id: Mapped[int] = mapped_column(primary_key=True)

    identificador: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )

    titulo: Mapped[str] = mapped_column(String(500))
    descricao: Mapped[str | None] = mapped_column(String(2000))

    tipo_suporte: Mapped[TipoSuporte] = mapped_column(
        SAEnum(TipoSuporte), index=True
    )

    tipo_unidade: Mapped[TipoUnidade] = mapped_column(
        SAEnum(TipoUnidade), index=True
    )

    nivel_acesso: Mapped[NivelAcesso] = mapped_column(
        SAEnum(NivelAcesso),
        default=NivelAcesso.RESTRITO,
        index=True,
    )

    status: Mapped[StatusUnidade] = mapped_column(
        SAEnum(StatusUnidade),
        default=StatusUnidade.ATIVA,
        index=True,
    )

    # --------------------
    # Relações estruturais
    # --------------------

    id_unidade_pai: Mapped[int | None] = mapped_column(
        ForeignKey("unidades_acondicionamento.id"),
        nullable=True,
    )

    id_representa: Mapped[int | None] = mapped_column(
        ForeignKey("unidades_acondicionamento.id"),
        nullable=True,
    )

    unidade_pai = relationship(
        "UnidadeAcondicionamento",
        remote_side=[id],
        foreign_keys=[id_unidade_pai],
        backref="unidades_filhas",
    )

    representa = relationship(
        "UnidadeAcondicionamento",
        remote_side=[id],
        foreign_keys=[id_representa],
    )

    # --------------------
    # Auditoria
    # --------------------

    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    atualizado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )
