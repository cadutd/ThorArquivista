from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AcaoPermissao(StrEnum):
    CRIAR = "CRIAR"
    EDITAR = "EDITAR"
    CONSULTAR = "CONSULTAR"
    EXCLUIR = "EXCLUIR"


class PermissaoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codigo: str = Field(..., min_length=3, max_length=150)
    nome: str = Field(..., min_length=3, max_length=255)
    descricao: str | None = None
    modulo: str = Field(..., min_length=2, max_length=100)
    funcao: str = Field(..., min_length=2, max_length=100)
    acao: AcaoPermissao
    ativo: bool = True


class PermissaoCreate(PermissaoBase):
    pass


class PermissaoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    codigo: str | None = Field(default=None, min_length=3, max_length=150)
    nome: str | None = Field(default=None, min_length=3, max_length=255)
    descricao: str | None = None
    modulo: str | None = Field(default=None, min_length=2, max_length=100)
    funcao: str | None = Field(default=None, min_length=2, max_length=100)
    acao: AcaoPermissao | None = None
    ativo: bool | None = None


class PermissaoRead(PermissaoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    criado_em: datetime
    atualizado_em: datetime


class PermissaoList(BaseModel):
    items: list[PermissaoRead]
    total: int
    limit: int
    offset: int


class PerfilBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=80)
    nome: str = Field(..., min_length=3, max_length=150)
    descricao: str | None = None
    ativo: bool = True
    sistema: bool = False
    permissao_ids: list[uuid.UUID] = Field(default_factory=list)


class PerfilCreate(PerfilBase):
    pass


class PerfilUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=2, max_length=80)
    nome: str | None = Field(default=None, min_length=3, max_length=150)
    descricao: str | None = None
    ativo: bool | None = None
    sistema: bool | None = None
    permissao_ids: list[uuid.UUID] | None = None


class PerfilRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    nome: str
    descricao: str | None
    ativo: bool
    sistema: bool
    permissoes: list[PermissaoRead] = Field(default_factory=list)
    criado_em: datetime
    atualizado_em: datetime


class PerfilList(BaseModel):
    items: list[PerfilRead]
    total: int
    limit: int
    offset: int
