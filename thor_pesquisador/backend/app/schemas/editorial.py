import uuid
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal

Role = Literal["ADMIN", "GESTOR_INSTRUMENTOS", "EDITOR", "REVISOR", "CONSULTA_INTERNA", "PUBLICO_AUTENTICADO"]


class TransicaoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operacao_id: uuid.UUID
    versao: int = Field(ge=1)
    justificativa: str | None = Field(default=None, max_length=4000)


class AcessoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: uuid.UUID
    papel: str = Field(min_length=2, max_length=40, pattern=r"^[A-Z][A-Z0-9_]+$")
    instrumento_id: uuid.UUID | None = None


class ConcessaoLoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    usuario_id: uuid.UUID
    perfis: list[str] = Field(min_length=1, max_length=50)
    escopo: Literal["GLOBAL", "INSTRUMENTO"]
    instrumento_ids: list[uuid.UUID] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validar_escopo(self):
        if any(not perfil or len(perfil) > 40 for perfil in self.perfis):
            raise ValueError("Perfil invalido.")
        if len(set(self.perfis)) != len(self.perfis) or len(set(self.instrumento_ids)) != len(self.instrumento_ids):
            raise ValueError("Perfis e instrumentos nao podem se repetir.")
        if self.escopo == "GLOBAL" and self.instrumento_ids:
            raise ValueError("Escopo global nao permite instrumentos.")
        if self.escopo == "INSTRUMENTO" and not self.instrumento_ids:
            raise ValueError("Selecione ao menos um instrumento.")
        if len(self.perfis) * max(1, len(self.instrumento_ids)) > 1000:
            raise ValueError("Limite de 1000 concessoes por operacao.")
        return self
