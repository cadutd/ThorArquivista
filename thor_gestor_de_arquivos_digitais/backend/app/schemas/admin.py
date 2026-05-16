from __future__ import annotations

from pydantic import BaseModel, Field


class DigitosCodigoEstrutura(BaseModel):
    corredor: int = Field(default=2, ge=1, le=6)
    modulo: int = Field(default=2, ge=1, le=6)
    estante: int = Field(default=2, ge=1, le=6)


class ConfiguracaoEnderecamento(BaseModel):
    digitos_codigo_estrutura: DigitosCodigoEstrutura = Field(
        default_factory=DigitosCodigoEstrutura,
    )


class ConfiguracaoInstituicao(BaseModel):
    nome: str | None = Field(default=None, max_length=255)
    logotipo_data_url: str | None = Field(default=None, max_length=5000000)
