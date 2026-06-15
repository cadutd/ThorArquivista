from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class TipoMidiaArmazenamentoBase(BaseModel):
    nome: str = Field(..., max_length=255)
    descricao: str | None = None
    tempo_duracao_anos: int = Field(..., ge=1)
    periodicidade_checagem_meses: int = Field(..., ge=1)
    ativo: bool = True


class TipoMidiaArmazenamentoCreate(TipoMidiaArmazenamentoBase):
    pass


class TipoMidiaArmazenamentoUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=255)
    descricao: str | None = None
    tempo_duracao_anos: int | None = Field(default=None, ge=1)
    periodicidade_checagem_meses: int | None = Field(default=None, ge=1)
    ativo: bool | None = None


class TipoMidiaArmazenamentoOut(TipoMidiaArmazenamentoBase):
    id: uuid.UUID
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}


class TipoMidiaArmazenamentoPage(BaseModel):
    items: list[TipoMidiaArmazenamentoOut]
    total: int
    limit: int
    offset: int


class MidiaArmazenamentoBase(BaseModel):
    nome: str = Field(..., max_length=255)
    tipo_midia_id: uuid.UUID
    descricao: str | None = Field(default=None, max_length=2000)
    ativo: bool = True
    data_aquisicao: date | None = None
    data_inicio_uso: date | None = None
    data_validade: date | None = None
    ultima_checagem_integridade: datetime | None = None
    proxima_checagem_integridade: datetime | None = None
    capacidade_total_bytes: int | None = Field(default=None, ge=0)
    capacidade_utilizada_bytes: int | None = Field(default=None, ge=0)
    identificador_fisico: str | None = Field(default=None, max_length=255)


class MidiaArmazenamentoCreate(MidiaArmazenamentoBase):
    pass


class MidiaArmazenamentoUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=255)
    tipo_midia_id: uuid.UUID | None = None
    descricao: str | None = Field(default=None, max_length=2000)
    ativo: bool | None = None
    data_aquisicao: date | None = None
    data_inicio_uso: date | None = None
    data_validade: date | None = None
    ultima_checagem_integridade: datetime | None = None
    proxima_checagem_integridade: datetime | None = None
    capacidade_total_bytes: int | None = Field(default=None, ge=0)
    capacidade_utilizada_bytes: int | None = Field(default=None, ge=0)
    identificador_fisico: str | None = Field(default=None, max_length=255)


class MidiaArmazenamentoOut(MidiaArmazenamentoBase):
    id: int
    id_posicao_armazenamento: int | None = None
    tipo_midia: TipoMidiaArmazenamentoOut | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}


class MidiaArmazenamentoPage(BaseModel):
    items: list[MidiaArmazenamentoOut]
    total: int
    limit: int
    offset: int
