from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import (
    StatusInstrumentoPesquisa,
    TipoInstrumentoPesquisa,
    VisibilidadeInstrumentoPesquisa,
)
from app.schemas.instrumento_campo import InstrumentoCampoSchema


class InstrumentoPesquisaBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    tipo: TipoInstrumentoPesquisa
    descricao: str | None = None
    status: StatusInstrumentoPesquisa = StatusInstrumentoPesquisa.RASCUNHO
    visibilidade: VisibilidadeInstrumentoPesquisa = VisibilidadeInstrumentoPesquisa.INTERNO
    responsavel: str | None = Field(default=None, max_length=255)


class InstrumentoPesquisaCreate(InstrumentoPesquisaBase):
    pass


class InstrumentoPesquisaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    tipo: TipoInstrumentoPesquisa | None = None
    descricao: str | None = None
    status: StatusInstrumentoPesquisa | None = None
    visibilidade: VisibilidadeInstrumentoPesquisa | None = None
    responsavel: str | None = Field(default=None, max_length=255)


class InstrumentoPesquisaOut(InstrumentoPesquisaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime


class InstrumentoPesquisaPage(BaseModel):
    items: list[InstrumentoPesquisaOut]
    total: int
    limit: int
    offset: int


class InstrumentoPesquisaSchemaResumo(BaseModel):
    id: uuid.UUID
    nome: str
    tipo: TipoInstrumentoPesquisa
    status: StatusInstrumentoPesquisa


class InstrumentoPesquisaSchema(BaseModel):
    instrumento: InstrumentoPesquisaSchemaResumo
    campos: list[InstrumentoCampoSchema]
