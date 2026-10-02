from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BuscaAvancadaIn(BaseModel):
    q: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    sort: list[str] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class BuscaAvancadaItem(BaseModel):
    id: str
    instrumento_id: str
    schema_version: int
    titulo: str
    texto_geral: str
    dados: dict[str, Any]
    status: str
    criado_em: datetime | str
    atualizado_em: datetime | str


class BuscaAvancadaOut(BaseModel):
    items: list[BuscaAvancadaItem]
    total: int
    limit: int
    offset: int
    indice_atualizado_em: datetime | None = None
    indice_defasado: bool = True


class FacetasOut(BaseModel):
    instrumento_id: uuid.UUID
    facetas: dict[str, dict[str, int]]


class ReindexacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    instrumento_id: uuid.UUID
    tipo: str
    status: str
    total_estimado: int
    processados: int
    ultimo_cursor_mongodb: str | None = None
    erro: str | None = None
    criado_em: datetime
    atualizado_em: datetime
