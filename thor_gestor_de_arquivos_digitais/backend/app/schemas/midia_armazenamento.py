from __future__ import annotations

from pydantic import BaseModel, Field
from app.models.enums import TipoMidiaArmazenamento


class MidiaArmazenamentoBase(BaseModel):
    nome: str = Field(..., max_length=255)
    tipo: TipoMidiaArmazenamento
    descricao: str | None = Field(default=None, max_length=2000)
    ativo: bool = True


class MidiaArmazenamentoCreate(MidiaArmazenamentoBase):
    pass


class MidiaArmazenamentoUpdate(BaseModel):
    nome: str | None = Field(default=None, max_length=255)
    tipo: TipoMidiaArmazenamento | None = None
    descricao: str | None = Field(default=None, max_length=2000)
    ativo: bool | None = None


class MidiaArmazenamentoOut(MidiaArmazenamentoBase):
    id: int
    id_posicao_armazenamento: int | None = None
    criado_em: str | None = None

    model_config = {"from_attributes": True}
