from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.enums import FuncaoCopia, StatusCopia


class CopiaUnidadeAcondicionamentoDigitalBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id_midia_armazenamento: int = Field(..., ge=1)

    uri_copia: str = Field(..., max_length=1200)
    funcao_copia: FuncaoCopia
    status_copia: StatusCopia = StatusCopia.ATIVA

    algoritmo_fixidez: str | None = Field(default=None, max_length=32)
    hash_fixidez: str | None = Field(default=None, max_length=128)
    ultima_verificacao_em: datetime | None = None


class CopiaUnidadeAcondicionamentoDigitalCreate(CopiaUnidadeAcondicionamentoDigitalBase):
    pass


class CopiaUnidadeAcondicionamentoDigitalUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status_copia: StatusCopia | None = None
    algoritmo_fixidez: str | None = Field(default=None, max_length=32)
    hash_fixidez: str | None = Field(default=None, max_length=128)
    ultima_verificacao_em: datetime | None = None


class CopiaUnidadeAcondicionamentoDigitalOut(CopiaUnidadeAcondicionamentoDigitalBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    id_unidade_acondicionamento: int
    id_posicao_armazenamento: int | None = None
    criada_em: datetime | None = None
