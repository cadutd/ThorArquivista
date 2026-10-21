import uuid
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.enums import TipoCampo


class NovoCampoImportacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str = Field(min_length=1, max_length=255)
    chave: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    tipo: TipoCampo
    obrigatorio: bool = False

    @model_validator(mode="after")
    def nome_valido(self):
        if not self.nome.strip() or "\x00" in self.nome:
            raise ValueError("Informe um nome de campo valido.")
        return self


class MapeamentoImportacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origem: str = Field(min_length=1, max_length=255)
    destino: str | None = Field(default=None, max_length=100)
    novo: NovoCampoImportacao | None = None

    @model_validator(mode="after")
    def alvo_unico(self):
        if bool(self.destino) == bool(self.novo):
            raise ValueError("Selecione um campo existente ou um novo campo.")
        return self


class ConfiguracaoImportacao(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operacao_id: uuid.UUID
    schema_version: int = Field(ge=1)
    mapeamentos: list[MapeamentoImportacao] = Field(min_length=1, max_length=100)
