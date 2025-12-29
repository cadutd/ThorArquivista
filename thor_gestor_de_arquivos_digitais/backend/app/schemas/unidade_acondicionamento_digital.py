from __future__ import annotations

from pydantic import BaseModel, Field


class UnidadeAcondicionamentoDigitalBase(BaseModel):
    tamanho_bytes: int | None = Field(default=None, ge=0)
    status_fixidez: str | None = Field(default=None, max_length=50)


class UnidadeAcondicionamentoDigitalCreate(UnidadeAcondicionamentoDigitalBase):
    id_unidade_acondicionamento: int


class UnidadeAcondicionamentoDigitalOut(UnidadeAcondicionamentoDigitalBase):
    id_unidade_acondicionamento: int

    model_config = {"from_attributes": True}
