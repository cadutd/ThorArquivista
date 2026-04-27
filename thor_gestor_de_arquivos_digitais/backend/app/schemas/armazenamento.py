from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    TipoCompartimentoArmazenamento,
    TipoEstruturaArmazenamento,
    TipoLocalGuarda,
    TipoPosicaoArmazenamento,
    TipoZonaGuarda,
)


class LocalGuardaBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codigo: str = Field(..., max_length=50)
    nome: str = Field(..., max_length=255)
    tipo_local: TipoLocalGuarda
    descricao: str | None = None
    logradouro: str | None = Field(default=None, max_length=255)
    numero: str | None = Field(default=None, max_length=50)
    complemento: str | None = Field(default=None, max_length=255)
    bairro: str | None = Field(default=None, max_length=120)
    municipio: str | None = Field(default=None, max_length=120)
    uf: str | None = Field(default=None, min_length=2, max_length=2)
    cep: str | None = Field(default=None, max_length=20)
    pais: str | None = Field(default="Brasil", max_length=120)
    observacoes: str | None = None
    ativo: bool = True


class LocalGuardaCreate(LocalGuardaBase):
    pass


class LocalGuardaUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codigo: str | None = Field(default=None, max_length=50)
    nome: str | None = Field(default=None, max_length=255)
    tipo_local: TipoLocalGuarda | None = None
    descricao: str | None = None
    logradouro: str | None = Field(default=None, max_length=255)
    numero: str | None = Field(default=None, max_length=50)
    complemento: str | None = Field(default=None, max_length=255)
    bairro: str | None = Field(default=None, max_length=120)
    municipio: str | None = Field(default=None, max_length=120)
    uf: str | None = Field(default=None, min_length=2, max_length=2)
    cep: str | None = Field(default=None, max_length=20)
    pais: str | None = Field(default=None, max_length=120)
    observacoes: str | None = None
    ativo: bool | None = None


class LocalGuardaRead(LocalGuardaBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None


class ZonaGuardaBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_local_guarda: int = Field(..., ge=1)
    codigo: str = Field(..., max_length=50)
    nome: str = Field(..., max_length=255)
    tipo_zona: TipoZonaGuarda
    descricao: str | None = None
    quantidade_corredores: int | None = Field(default=None, gt=0)
    quantidade_modulos_por_corredor: int | None = Field(default=None, gt=0)
    quantidade_estantes_por_modulo: int | None = Field(default=None, gt=0)
    quantidade_prateleiras_por_estante: int | None = Field(default=None, gt=0)
    capacidade_caixas_por_prateleira: int | None = Field(default=None, gt=0)
    observacoes: str | None = None
    ativo: bool = True


class ZonaGuardaCreate(ZonaGuardaBase):
    pass


class ZonaGuardaUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_local_guarda: int | None = Field(default=None, ge=1)
    codigo: str | None = Field(default=None, max_length=50)
    nome: str | None = Field(default=None, max_length=255)
    tipo_zona: TipoZonaGuarda | None = None
    descricao: str | None = None
    quantidade_corredores: int | None = Field(default=None, gt=0)
    quantidade_modulos_por_corredor: int | None = Field(default=None, gt=0)
    quantidade_estantes_por_modulo: int | None = Field(default=None, gt=0)
    quantidade_prateleiras_por_estante: int | None = Field(default=None, gt=0)
    capacidade_caixas_por_prateleira: int | None = Field(default=None, gt=0)
    observacoes: str | None = None
    ativo: bool | None = None


class ZonaGuardaRead(ZonaGuardaBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    local_guarda_nome: str | None = None
    topografia_gerada: bool = False
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None


class EstruturaArmazenamentoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_zona_guarda: int = Field(..., ge=1)
    codigo: str = Field(..., max_length=50)
    nome: str = Field(..., max_length=255)
    tipo_estrutura: TipoEstruturaArmazenamento
    descricao: str | None = None
    ordem: int | None = Field(default=None, gt=0)
    capacidade_total: int | None = Field(default=None, gt=0)
    observacoes: str | None = None
    ativo: bool = True


class EstruturaArmazenamentoCreate(EstruturaArmazenamentoBase):
    pass


class EstruturaArmazenamentoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_zona_guarda: int | None = Field(default=None, ge=1)
    codigo: str | None = Field(default=None, max_length=50)
    nome: str | None = Field(default=None, max_length=255)
    tipo_estrutura: TipoEstruturaArmazenamento | None = None
    descricao: str | None = None
    ordem: int | None = Field(default=None, gt=0)
    capacidade_total: int | None = Field(default=None, gt=0)
    observacoes: str | None = None
    ativo: bool | None = None


class EstruturaArmazenamentoRead(EstruturaArmazenamentoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    zona_nome: str | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None


class CompartimentoArmazenamentoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_estrutura_armazenamento: int = Field(..., ge=1)
    codigo: str = Field(..., max_length=50)
    nome: str = Field(..., max_length=255)
    tipo_compartimento: TipoCompartimentoArmazenamento
    descricao: str | None = None
    ordem: int | None = Field(default=None, gt=0)
    capacidade_posicoes: int | None = Field(default=None, gt=0)
    observacoes: str | None = None
    ativo: bool = True


class CompartimentoArmazenamentoCreate(CompartimentoArmazenamentoBase):
    pass


class CompartimentoArmazenamentoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_estrutura_armazenamento: int | None = Field(default=None, ge=1)
    codigo: str | None = Field(default=None, max_length=50)
    nome: str | None = Field(default=None, max_length=255)
    tipo_compartimento: TipoCompartimentoArmazenamento | None = None
    descricao: str | None = None
    ordem: int | None = Field(default=None, gt=0)
    capacidade_posicoes: int | None = Field(default=None, gt=0)
    observacoes: str | None = None
    ativo: bool | None = None


class CompartimentoArmazenamentoRead(CompartimentoArmazenamentoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    estrutura_nome: str | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None


class PosicaoArmazenamentoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_compartimento_armazenamento: int = Field(..., ge=1)
    codigo: str = Field(..., max_length=50)
    codigo_completo: str = Field(..., max_length=500)
    tipo_posicao: TipoPosicaoArmazenamento
    ordem: int | None = Field(default=None, gt=0)
    capacidade_unidades: int = Field(default=1, gt=0)
    ocupada: bool = False
    ativo: bool = True
    observacoes: str | None = None


class PosicaoArmazenamentoCreate(PosicaoArmazenamentoBase):
    pass


class PosicaoArmazenamentoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_compartimento_armazenamento: int | None = Field(default=None, ge=1)
    codigo: str | None = Field(default=None, max_length=50)
    codigo_completo: str | None = Field(default=None, max_length=500)
    tipo_posicao: TipoPosicaoArmazenamento | None = None
    ordem: int | None = Field(default=None, gt=0)
    capacidade_unidades: int | None = Field(default=None, gt=0)
    ocupada: bool | None = None
    ativo: bool | None = None
    observacoes: str | None = None


class PosicaoArmazenamentoRead(PosicaoArmazenamentoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    local_guarda: str | None = None
    zona: str | None = None
    localizacao_completa: str | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None


class MovimentacaoArmazenamentoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_unidade_acondicionamento: int | None = None
    id_midia_armazenamento: int | None = None
    id_copia_unidade_acondicionamento_digital: int | None = None
    id_posicao_origem: int | None = None
    id_posicao_destino: int | None = None
    data_movimentacao: datetime | None = None
    responsavel: str | None = None
    motivo: str | None = None
    observacoes: str | None = None


class AtribuirPosicaoRequest(BaseModel):
    id_posicao: int = Field(..., ge=1)
    responsavel: str | None = Field(default=None, max_length=255)
    motivo: str | None = None
    observacoes: str | None = None


class TopografiaGeradaRead(BaseModel):
    id_zona_guarda: int
    estruturas_criadas: int
    compartimentos_criados: int
    posicoes_criadas: int


class OcupacaoRead(BaseModel):
    id: int
    nome: str
    total_posicoes: int
    posicoes_ocupadas: int
    capacidade_total: int
    ocupacao_total: int
    taxa_ocupacao: float
