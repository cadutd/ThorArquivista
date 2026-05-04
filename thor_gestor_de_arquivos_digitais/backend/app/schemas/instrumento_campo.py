from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TipoCampoInstrumento


class InstrumentoCampoBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=255)
    chave: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    tipo: TipoCampoInstrumento
    ordem: int = Field(default=0, ge=0)
    obrigatorio: bool = False
    multiplo: bool = False
    valor_padrao: str | None = None
    placeholder: str | None = None
    ajuda: str | None = None
    aparece_cadastro: bool = True
    aparece_listagem: bool = True
    aparece_busca: bool = True
    filtro_avancado: bool = False
    facetavel: bool = False
    ordenavel: bool = False
    opcoes: dict[str, Any] | list[Any] | None = None
    validacoes: dict[str, Any] | list[Any] | None = None


class InstrumentoCampoCreate(InstrumentoCampoBase):
    pass


class InstrumentoCampoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    chave: str | None = Field(default=None, min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    tipo: TipoCampoInstrumento | None = None
    ordem: int | None = Field(default=None, ge=0)
    obrigatorio: bool | None = None
    multiplo: bool | None = None
    valor_padrao: str | None = None
    placeholder: str | None = None
    ajuda: str | None = None
    aparece_cadastro: bool | None = None
    aparece_listagem: bool | None = None
    aparece_busca: bool | None = None
    filtro_avancado: bool | None = None
    facetavel: bool | None = None
    ordenavel: bool | None = None
    opcoes: dict[str, Any] | list[Any] | None = None
    validacoes: dict[str, Any] | list[Any] | None = None


class InstrumentoCampoOut(InstrumentoCampoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    instrumento_id: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime


class InstrumentoCampoSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    chave: str
    tipo: TipoCampoInstrumento
    ordem: int
    obrigatorio: bool
    multiplo: bool
    placeholder: str | None = None
    ajuda: str | None = None
    opcoes: dict[str, Any] | list[Any] | None = None
    validacoes: dict[str, Any] | list[Any] | None = None
    aparece_cadastro: bool
    aparece_listagem: bool
    aparece_busca: bool
    filtro_avancado: bool


class InstrumentoCampoReordenarItem(BaseModel):
    id: uuid.UUID
    ordem: int = Field(..., ge=0)


class InstrumentoCampoReordenar(BaseModel):
    campos: list[InstrumentoCampoReordenarItem] = Field(..., min_length=1)
