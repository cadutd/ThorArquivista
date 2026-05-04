from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StatusInstrumentoRegistro(str, Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    EXCLUIDO = "EXCLUIDO"


class InstrumentoRegistroBase(BaseModel):
    dados: dict[str, Any] = Field(default_factory=dict)
    unidade_acondicionamento_ids: list[int] = Field(default_factory=list)
    registro_descritivo_ids: list[str] = Field(default_factory=list)
    status: StatusInstrumentoRegistro = StatusInstrumentoRegistro.ATIVO


class InstrumentoRegistroCreate(InstrumentoRegistroBase):
    pass


class InstrumentoRegistroUpdate(InstrumentoRegistroBase):
    pass


class InstrumentoRegistroOut(InstrumentoRegistroBase):
    id: str
    instrumento_id: str
    schema_version: int
    criado_em: datetime
    atualizado_em: datetime


class InstrumentoRegistroPage(BaseModel):
    items: list[InstrumentoRegistroOut]
    page_size: int
    next_cursor: str | None = None
    has_more: bool = False
