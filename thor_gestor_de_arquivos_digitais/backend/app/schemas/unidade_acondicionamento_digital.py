from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict


class UnidadeAcondicionamentoDigitalBase(BaseModel):
    model_config = ConfigDict()

    tamanho_bytes: int | None = Field(default=None, ge=0)
    status_fixidez: str | None = Field(default=None, max_length=50)


class UnidadeAcondicionamentoDigitalCreate(UnidadeAcondicionamentoDigitalBase):
    id_unidade_acondicionamento: int = Field(..., ge=1)


class UnidadeAcondicionamentoDigitalOut(UnidadeAcondicionamentoDigitalBase):
    model_config = ConfigDict(from_attributes=True)

    id_unidade_acondicionamento: int
