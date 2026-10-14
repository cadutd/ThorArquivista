from pydantic import BaseModel, ConfigDict, Field


class PerfilIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    codigo: str = Field(min_length=2, max_length=40, pattern=r"^[A-Z][A-Z0-9_]+$")
    nome: str = Field(min_length=3, max_length=150)
    descricao: str | None = Field(default=None, max_length=4000)
    ativo: bool = True
    permissoes: list[str] = Field(default_factory=list, max_length=30)
