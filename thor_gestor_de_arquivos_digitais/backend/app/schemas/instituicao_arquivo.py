from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EsferaAdministrativa


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InstituicaoArquivoBase(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    nome: str = Field(..., min_length=1, max_length=255)
    sigla: str | None = Field(default=None, max_length=50)
    codigo_referencia: str | None = Field(default=None, max_length=100)
    natureza_juridica: str | None = Field(default=None, max_length=100)
    esfera_administrativa: EsferaAdministrativa | None = None
    cnpj: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=50)
    site: str | None = Field(default=None, max_length=255)
    endereco_logradouro: str | None = Field(default=None, max_length=255)
    endereco_numero: str | None = Field(default=None, max_length=50)
    endereco_complemento: str | None = Field(default=None, max_length=100)
    endereco_bairro: str | None = Field(default=None, max_length=100)
    endereco_municipio: str | None = Field(default=None, max_length=100)
    endereco_uf: str | None = Field(default=None, min_length=2, max_length=2)
    endereco_cep: str | None = Field(default=None, max_length=20)
    endereco_pais: str | None = Field(default="Brasil", max_length=100)
    responsavel_nome: str | None = Field(default=None, max_length=255)
    responsavel_cargo: str | None = Field(default=None, max_length=255)
    responsavel_email: str | None = Field(default=None, max_length=255)
    responsavel_telefone: str | None = Field(default=None, max_length=50)
    historico: str | None = None
    missao: str | None = None
    observacoes: str | None = None

    @field_validator("email", "responsavel_email")
    @classmethod
    def validar_email(cls, value: str | None):
        if value and not EMAIL_PATTERN.match(value):
            raise ValueError("Informe um e-mail válido.")
        return value

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, value: str | None):
        if not value:
            return value
        digits = re.sub(r"\D", "", value)
        if len(digits) != 14 or digits == digits[0] * 14:
            raise ValueError("Informe um CNPJ válido.")

        def digit(numbers: str) -> str:
            weights = list(range(len(numbers) - 7, 1, -1)) + list(range(9, 1, -1))
            total = sum(int(number) * weight for number, weight in zip(numbers, weights, strict=False))
            remainder = total % 11
            return "0" if remainder < 2 else str(11 - remainder)

        if digits[12] != digit(digits[:12]) or digits[13] != digit(digits[:13]):
            raise ValueError("Informe um CNPJ válido.")
        return value


class InstituicaoArquivoCreate(InstituicaoArquivoBase):
    pass


class InstituicaoArquivoUpdate(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    nome: str | None = Field(default=None, min_length=1, max_length=255)
    sigla: str | None = Field(default=None, max_length=50)
    codigo_referencia: str | None = Field(default=None, max_length=100)
    natureza_juridica: str | None = Field(default=None, max_length=100)
    esfera_administrativa: EsferaAdministrativa | None = None
    cnpj: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=50)
    site: str | None = Field(default=None, max_length=255)
    endereco_logradouro: str | None = Field(default=None, max_length=255)
    endereco_numero: str | None = Field(default=None, max_length=50)
    endereco_complemento: str | None = Field(default=None, max_length=100)
    endereco_bairro: str | None = Field(default=None, max_length=100)
    endereco_municipio: str | None = Field(default=None, max_length=100)
    endereco_uf: str | None = Field(default=None, min_length=2, max_length=2)
    endereco_cep: str | None = Field(default=None, max_length=20)
    endereco_pais: str | None = Field(default=None, max_length=100)
    responsavel_nome: str | None = Field(default=None, max_length=255)
    responsavel_cargo: str | None = Field(default=None, max_length=255)
    responsavel_email: str | None = Field(default=None, max_length=255)
    responsavel_telefone: str | None = Field(default=None, max_length=50)
    historico: str | None = None
    missao: str | None = None
    observacoes: str | None = None

    _validar_email = field_validator("email", "responsavel_email")(
        InstituicaoArquivoBase.validar_email
    )
    _validar_cnpj = field_validator("cnpj")(InstituicaoArquivoBase.validar_cnpj)


class InstituicaoArquivoRead(InstituicaoArquivoBase):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: uuid.UUID
    criada_em: datetime
    atualizada_em: datetime
