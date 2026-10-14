import uuid
from pydantic import BaseModel, Field, ConfigDict
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
