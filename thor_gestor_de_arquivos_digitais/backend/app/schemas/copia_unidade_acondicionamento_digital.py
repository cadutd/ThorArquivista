from __future__ import annotations

from pydantic import BaseModel, Field
from app.models.enums import FuncaoCopia, StatusCopia


class CopiaUnidadeAcondicionamentoDigitalBase(BaseModel):
    id_unidade_acondicionamento: int
    id_midia_armazenamento: int

    uri_copia: str = Field(..., max_length=1200)
    funcao_copia: FuncaoCopia
    status_copia: StatusCopia = StatusCopia.ATIVA

    algoritmo_fixidez: str | None = Field(default=None, max_length=32)
    hash_fixidez: str | None = Field(default=None, max_length=128)
    ultima_verificacao_em: str | None = None


class CopiaUnidadeAcondicionamentoDigitalCreate(CopiaUnidadeAcondicionamentoDigitalBase):
    pass


class CopiaUnidadeAcondicionamentoDigitalUpdate(BaseModel):
    status_copia: StatusCopia | None = None
    algoritmo_fixidez: str | None = Field(default=None, max_length=32)
    hash_fixidez: str | None = Field(default=None, max_length=128)
    ultima_verificacao_em: str | None = None


class CopiaUnidadeAcondicionamentoDigitalOut(CopiaUnidadeAcondicionamentoDigitalBase):
    id: int
    criada_em: str | None = None

    model_config = {"from_attributes": True}
