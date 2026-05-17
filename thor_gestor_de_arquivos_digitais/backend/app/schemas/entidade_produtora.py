from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import TipoEntidadeProdutora


class EntidadeProdutoraBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    nome: str = Field(..., min_length=1, max_length=255)
    sigla: str | None = Field(default=None, max_length=50)
    codigo_referencia: str | None = Field(default=None, max_length=100)
    tipo_entidade: TipoEntidadeProdutora
    natureza_juridica: str | None = Field(default=None, max_length=100)
    data_inicio: date | None = None
    data_fim: date | None = None
    entidade_ativa: bool = True
    historico: str | None = None
    competencias_funcoes: str | None = None
    observacoes: str | None = None
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=50)
    site: str | None = Field(default=None, max_length=255)
    endereco_logradouro: str | None = Field(default=None, max_length=255)
    endereco_numero: str | None = Field(default=None, max_length=50)
    endereco_complemento: str | None = Field(default=None, max_length=100)
    endereco_bairro: str | None = Field(default=None, max_length=100)
    endereco_municipio: str | None = Field(default=None, max_length=100)
    endereco_uf: str | None = Field(default=None, min_length=2, max_length=2)
    endereco_cep: str | None = Field(default=None, max_length=20)
    endereco_pais: str | None = Field(default="Brasil", max_length=100)
    id_entidade_superior: uuid.UUID | None = None

    @model_validator(mode="after")
    def validar_datas(self):
        if self.data_inicio and self.data_fim and self.data_fim < self.data_inicio:
            raise ValueError("data_fim não pode ser anterior a data_inicio.")
        if self.data_fim and self.entidade_ativa and not (self.observacoes or "").strip():
            raise ValueError(
                "Informe observacoes para manter a entidade ativa com data_fim preenchida."
            )
        return self


class EntidadeProdutoraCreate(EntidadeProdutoraBase):
    pass


class EntidadeProdutoraUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    sigla: str | None = Field(default=None, max_length=50)
    codigo_referencia: str | None = Field(default=None, max_length=100)
    tipo_entidade: TipoEntidadeProdutora | None = None
    natureza_juridica: str | None = Field(default=None, max_length=100)
    data_inicio: date | None = None
    data_fim: date | None = None
    entidade_ativa: bool | None = None
    historico: str | None = None
    competencias_funcoes: str | None = None
    observacoes: str | None = None
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=50)
    site: str | None = Field(default=None, max_length=255)
    endereco_logradouro: str | None = Field(default=None, max_length=255)
    endereco_numero: str | None = Field(default=None, max_length=50)
    endereco_complemento: str | None = Field(default=None, max_length=100)
    endereco_bairro: str | None = Field(default=None, max_length=100)
    endereco_municipio: str | None = Field(default=None, max_length=100)
    endereco_uf: str | None = Field(default=None, min_length=2, max_length=2)
    endereco_cep: str | None = Field(default=None, max_length=20)
    endereco_pais: str | None = Field(default=None, max_length=100)
    id_entidade_superior: uuid.UUID | None = None


class EntidadeProdutoraRead(EntidadeProdutoraBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    nome_normalizado: str | None = None
    nome_entidade_superior: str | None = None
    criado_em: datetime
    atualizado_em: datetime
    avisos_duplicidade: list[str] = Field(default_factory=list)


class EntidadeProdutoraList(BaseModel):
    items: list[EntidadeProdutoraRead]
    total: int
    limit: int
    offset: int


class EntidadeProdutoraTree(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    nome: str
    sigla: str | None = None
    codigo_referencia: str | None = None
    tipo_entidade: TipoEntidadeProdutora
    entidade_ativa: bool
    id_entidade_superior: uuid.UUID | None = None
    has_children: bool = False
    filhos: list["EntidadeProdutoraTree"] = Field(default_factory=list)
