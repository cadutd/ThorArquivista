from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import StatusRegistro


class RegistroBase(BaseModel):
    dados: dict[str, Any] = Field(default_factory=dict)
    status: StatusRegistro = StatusRegistro.ATIVO


class RegistroCreate(RegistroBase):
    pass


class RegistroUpdate(RegistroBase):
    pass


class RegistroOut(RegistroBase):
    id: str
    instrumento_id: str
    schema_version: int
    criado_por: str | None = None
    atualizado_por: str | None = None
    criado_em: datetime
    atualizado_em: datetime


class RegistroPage(BaseModel):
    items: list[RegistroOut]
    page_size: int
    next_cursor: str | None = None
    has_more: bool = False


class RegistroSearch(BaseModel):
    q: str = Field(min_length=1)
    page_size: int = Field(default=50, ge=1, le=100)
    cursor: str | None = None
