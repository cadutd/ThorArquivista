from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    TipoCompartimentoArmazenamento,
    TipoEstruturaArmazenamento,
    TipoLocalGuarda,
    TipoPosicaoArmazenamento,
    TipoZonaGuarda,
)


class LocalGuarda(Base):
    __tablename__ = "locais_guarda"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_local: Mapped[TipoLocalGuarda] = mapped_column(
        SAEnum(TipoLocalGuarda, name="tipo_local_guarda"),
        nullable=False,
    )
    descricao: Mapped[str | None] = mapped_column(Text)
    logradouro: Mapped[str | None] = mapped_column(String(255))
    numero: Mapped[str | None] = mapped_column(String(50))
    complemento: Mapped[str | None] = mapped_column(String(255))
    bairro: Mapped[str | None] = mapped_column(String(120))
    municipio: Mapped[str | None] = mapped_column(String(120))
    uf: Mapped[str | None] = mapped_column(String(2))
    cep: Mapped[str | None] = mapped_column(String(20))
    pais: Mapped[str | None] = mapped_column(String(120), default="Brasil")
    observacoes: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    zonas = relationship(
        "ZonaGuarda",
        back_populates="local_guarda",
        cascade="all, delete-orphan",
    )


class ZonaGuarda(Base):
    __tablename__ = "zonas_guarda"
    __table_args__ = (
        UniqueConstraint("id_local_guarda", "codigo", name="uq_zona_por_local"),
        CheckConstraint(
            """
            (quantidade_corredores IS NULL OR quantidade_corredores > 0)
            AND (quantidade_modulos_por_corredor IS NULL OR quantidade_modulos_por_corredor > 0)
            AND (quantidade_estantes_por_modulo IS NULL OR quantidade_estantes_por_modulo > 0)
            AND (quantidade_prateleiras_por_estante IS NULL OR quantidade_prateleiras_por_estante > 0)
            AND (capacidade_caixas_por_prateleira IS NULL OR capacidade_caixas_por_prateleira > 0)
            """,
            name="ck_zona_quantidades_positivas",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_local_guarda: Mapped[int] = mapped_column(
        ForeignKey("locais_guarda.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_zona: Mapped[TipoZonaGuarda] = mapped_column(
        SAEnum(TipoZonaGuarda, name="tipo_zona_guarda"),
        nullable=False,
    )
    descricao: Mapped[str | None] = mapped_column(Text)
    quantidade_corredores: Mapped[int | None] = mapped_column(Integer)
    quantidade_modulos_por_corredor: Mapped[int | None] = mapped_column(Integer)
    quantidade_estantes_por_modulo: Mapped[int | None] = mapped_column(Integer)
    quantidade_prateleiras_por_estante: Mapped[int | None] = mapped_column(Integer)
    capacidade_caixas_por_prateleira: Mapped[int | None] = mapped_column(Integer)
    observacoes: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    local_guarda = relationship("LocalGuarda", back_populates="zonas")
    estruturas = relationship(
        "EstruturaArmazenamento",
        back_populates="zona_guarda",
        cascade="all, delete-orphan",
    )


class EstruturaArmazenamento(Base):
    __tablename__ = "estruturas_armazenamento"
    __table_args__ = (
        UniqueConstraint("id_zona_guarda", "codigo", name="uq_estrutura_por_zona"),
        CheckConstraint("ordem IS NULL OR ordem > 0", name="ck_estrutura_ordem_positiva"),
        CheckConstraint(
            "capacidade_total IS NULL OR capacidade_total > 0",
            name="ck_estrutura_capacidade_positiva",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_zona_guarda: Mapped[int] = mapped_column(
        ForeignKey("zonas_guarda.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_estrutura: Mapped[TipoEstruturaArmazenamento] = mapped_column(
        SAEnum(TipoEstruturaArmazenamento, name="tipo_estrutura_armazenamento"),
        nullable=False,
    )
    descricao: Mapped[str | None] = mapped_column(Text)
    ordem: Mapped[int | None] = mapped_column(Integer)
    capacidade_total: Mapped[int | None] = mapped_column(Integer)
    observacoes: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    zona_guarda = relationship("ZonaGuarda", back_populates="estruturas")
    compartimentos = relationship(
        "CompartimentoArmazenamento",
        back_populates="estrutura_armazenamento",
        cascade="all, delete-orphan",
    )


class CompartimentoArmazenamento(Base):
    __tablename__ = "compartimentos_armazenamento"
    __table_args__ = (
        UniqueConstraint(
            "id_estrutura_armazenamento",
            "codigo",
            name="uq_compartimento_por_estrutura",
        ),
        CheckConstraint("ordem IS NULL OR ordem > 0", name="ck_compartimento_ordem_positiva"),
        CheckConstraint(
            "capacidade_posicoes IS NULL OR capacidade_posicoes > 0",
            name="ck_compartimento_capacidade_positiva",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_estrutura_armazenamento: Mapped[int] = mapped_column(
        ForeignKey("estruturas_armazenamento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo_compartimento: Mapped[TipoCompartimentoArmazenamento] = mapped_column(
        SAEnum(TipoCompartimentoArmazenamento, name="tipo_compartimento_armazenamento"),
        nullable=False,
    )
    descricao: Mapped[str | None] = mapped_column(Text)
    ordem: Mapped[int | None] = mapped_column(Integer)
    capacidade_posicoes: Mapped[int | None] = mapped_column(Integer)
    observacoes: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    estrutura_armazenamento = relationship(
        "EstruturaArmazenamento",
        back_populates="compartimentos",
    )
    posicoes = relationship(
        "PosicaoArmazenamento",
        back_populates="compartimento_armazenamento",
        cascade="all, delete-orphan",
    )


class PosicaoArmazenamento(Base):
    __tablename__ = "posicoes_armazenamento"
    __table_args__ = (
        UniqueConstraint(
            "id_compartimento_armazenamento",
            "codigo",
            name="uq_posicao_por_compartimento",
        ),
        CheckConstraint("ordem IS NULL OR ordem > 0", name="ck_posicao_ordem_positiva"),
        CheckConstraint("capacidade_unidades > 0", name="ck_posicao_capacidade_positiva"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_compartimento_armazenamento: Mapped[int] = mapped_column(
        ForeignKey("compartimentos_armazenamento.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    codigo_completo: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    tipo_posicao: Mapped[TipoPosicaoArmazenamento] = mapped_column(
        SAEnum(TipoPosicaoArmazenamento, name="tipo_posicao_armazenamento"),
        nullable=False,
    )
    ordem: Mapped[int | None] = mapped_column(Integer)
    capacidade_unidades: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ocupada: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    atualizado_em: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    compartimento_armazenamento = relationship(
        "CompartimentoArmazenamento",
        back_populates="posicoes",
    )
    unidades = relationship("UnidadeAcondicionamento", back_populates="posicao_armazenamento")
    midias = relationship("MidiaArmazenamento", back_populates="posicao_armazenamento")
    copias = relationship(
        "CopiaUnidadeAcondicionamentoDigital",
        back_populates="posicao_armazenamento",
    )
    movimentacoes_origem = relationship(
        "MovimentacaoArmazenamento",
        foreign_keys="MovimentacaoArmazenamento.id_posicao_origem",
        back_populates="posicao_origem",
    )
    movimentacoes_destino = relationship(
        "MovimentacaoArmazenamento",
        foreign_keys="MovimentacaoArmazenamento.id_posicao_destino",
        back_populates="posicao_destino",
    )

    @property
    def local_guarda(self) -> str | None:
        return self.compartimento_armazenamento.estrutura_armazenamento.zona_guarda.local_guarda.nome

    @property
    def zona(self) -> str | None:
        return self.compartimento_armazenamento.estrutura_armazenamento.zona_guarda.nome

    @property
    def localizacao_completa(self) -> str:
        compartimento = self.compartimento_armazenamento
        estrutura = compartimento.estrutura_armazenamento
        zona = estrutura.zona_guarda
        local = zona.local_guarda
        return " > ".join(
            [
                local.nome,
                zona.nome,
                estrutura.nome,
                compartimento.nome,
                self.codigo,
            ]
        )


class MovimentacaoArmazenamento(Base):
    __tablename__ = "movimentacoes_armazenamento"
    __table_args__ = (
        CheckConstraint(
            """
            (
                CASE WHEN id_unidade_acondicionamento IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN id_midia_armazenamento IS NOT NULL THEN 1 ELSE 0 END +
                CASE WHEN id_copia_unidade_acondicionamento_digital IS NOT NULL THEN 1 ELSE 0 END
            ) = 1
            """,
            name="ck_movimentacao_um_objeto",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    id_unidade_acondicionamento: Mapped[int | None] = mapped_column(
        ForeignKey("unidades_acondicionamento.id", ondelete="CASCADE"),
        index=True,
    )
    id_midia_armazenamento: Mapped[int | None] = mapped_column(
        ForeignKey("midias_armazenamento.id", ondelete="CASCADE"),
        index=True,
    )
    id_copia_unidade_acondicionamento_digital: Mapped[int | None] = mapped_column(
        ForeignKey("copias_unidades_acondicionamento_digitais.id", ondelete="CASCADE"),
        index=True,
    )
    id_posicao_origem: Mapped[int | None] = mapped_column(
        ForeignKey("posicoes_armazenamento.id", ondelete="SET NULL"),
    )
    id_posicao_destino: Mapped[int | None] = mapped_column(
        ForeignKey("posicoes_armazenamento.id", ondelete="SET NULL"),
    )
    data_movimentacao: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    responsavel: Mapped[str | None] = mapped_column(String(255))
    motivo: Mapped[str | None] = mapped_column(Text)
    observacoes: Mapped[str | None] = mapped_column(Text)

    unidade = relationship("UnidadeAcondicionamento")
    midia = relationship("MidiaArmazenamento")
    copia = relationship("CopiaUnidadeAcondicionamentoDigital")
    posicao_origem = relationship(
        "PosicaoArmazenamento",
        foreign_keys=[id_posicao_origem],
        back_populates="movimentacoes_origem",
    )
    posicao_destino = relationship(
        "PosicaoArmazenamento",
        foreign_keys=[id_posicao_destino],
        back_populates="movimentacoes_destino",
    )
