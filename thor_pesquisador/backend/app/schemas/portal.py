from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEFAULT_COLORS = {"primaria": "#0e6496", "secundaria": "#235347", "destaque": "#8f2453",
                  "fundo": "#ffffff", "texto": "#17232d"}


def luminancia(hex_color):
    values = [int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(v * weight for v, weight in zip(rgb, (.2126, .7152, .0722)))


def contraste(a, b):
    low, high = sorted((luminancia(a), luminancia(b)))
    return (high + .05) / (low + .05)


class CoresPortal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    primaria: str = DEFAULT_COLORS["primaria"]
    secundaria: str = DEFAULT_COLORS["secundaria"]
    destaque: str = DEFAULT_COLORS["destaque"]
    fundo: str = DEFAULT_COLORS["fundo"]
    texto: str = DEFAULT_COLORS["texto"]

    @field_validator("*")
    @classmethod
    def cor_hex(cls, value):
        import re
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError("Use uma cor hexadecimal no formato #RRGGBB.")
        return value.lower()

    @model_validator(mode="after")
    def contraste_acessivel(self):
        if contraste(self.texto, self.fundo) < 4.5:
            raise ValueError("Texto e fundo precisam de contraste minimo 4,5:1.")
        for key in ("primaria", "secundaria", "destaque"):
            if contraste(getattr(self, key), self.fundo) < 4.5:
                raise ValueError(f"A cor {key} precisa de contraste minimo 4,5:1 com o fundo.")
        return self


class ConfiguracaoPortalIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome_instituicao: str = Field(min_length=3, max_length=150)
    cores: CoresPortal
    versao: int = Field(ge=1)

    @field_validator("nome_instituicao")
    @classmethod
    def nome_valido(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Informe o nome da instituicao.")
        return value
