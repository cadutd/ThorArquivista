from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusInstrumento, TipoInstrumento, VisibilidadeInstrumento
from app.schemas.instrumento_campo import InstrumentoCampoOut


class InstrumentoBase(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    tipo: TipoInstrumento
    descricao: str | None = None
    status: StatusInstrumento = StatusInstrumento.RASCUNHO
    visibilidade: VisibilidadeInstrumento = VisibilidadeInstrumento.INTERNO


class InstrumentoCreate(InstrumentoBase):
    pass


class InstrumentoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    tipo: TipoInstrumento | None = None
    descricao: str | None = None
    status: StatusInstrumento | None = None
    visibilidade: VisibilidadeInstrumento | None = None


class InstrumentoOut(InstrumentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    schema_version: int
    criado_em: datetime
    atualizado_em: datetime


class InstrumentoPage(BaseModel):
    items: list[InstrumentoOut]
    total: int
    limit: int
    offset: int


class InstrumentoSchema(InstrumentoOut):
    campos: list[InstrumentoCampoOut]
