from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.services.cpf import normalizar_cpf


class UsuarioIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nome: str = Field(min_length=1, max_length=255)
    username: str = Field(min_length=3, max_length=150, pattern=r"^[a-zA-Z0-9_.-]+$")
    cpf: str
    email: EmailStr = Field(max_length=255)
    perfil_codigo: str = Field(min_length=1, max_length=40)
    ativo: bool = True
    observacoes: str | None = Field(default=None, max_length=4000)

    @field_validator("cpf")
    @classmethod
    def cpf_valido(cls, value):
        return normalizar_cpf(value)

    @field_validator("username")
    @classmethod
    def usuario_normalizado(cls, value):
        return value.lower()
