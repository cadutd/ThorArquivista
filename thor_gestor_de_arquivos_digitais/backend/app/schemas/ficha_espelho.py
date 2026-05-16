from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


CampoFichaEspelho = Literal[
    "logo_instituicao",
    "unidade_produtora",
    "fundo",
    "classe",
    "subclasse",
    "descricao_conteudo",
    "data_limite",
    "identificador_caixa",
    "codigo_barras",
]

CAMPOS_PADRAO_FICHA_ESPELHO: list[str] = [
    "logo_instituicao",
    "unidade_produtora",
    "fundo",
    "classe",
    "subclasse",
    "descricao_conteudo",
    "data_limite",
    "identificador_caixa",
    "codigo_barras",
]

PRINT_MARGIN_CM = 1.2
PRINT_COLUMN_GAP_CM = 0.2


def limites_modelo_ficha(
    tamanho_papel: str,
    orientacao: str,
    colunas: int,
) -> tuple[float, float]:
    largura, altura = (21.59, 27.94) if tamanho_papel == "CARTA" else (21.0, 29.7)
    if orientacao == "PAISAGEM":
        largura, altura = altura, largura
    largura_util = largura - (PRINT_MARGIN_CM * 2)
    altura_util = altura - (PRINT_MARGIN_CM * 2)
    largura_coluna = (largura_util - (PRINT_COLUMN_GAP_CM * max(0, colunas - 1))) / colunas
    return round(largura_coluna, 2), round(altura_util, 2)


def validar_dimensoes_modelo(
    tamanho_papel: str,
    orientacao: str,
    colunas: int,
    largura_cm: float,
    altura_cm: float,
) -> None:
    largura_maxima, altura_maxima = limites_modelo_ficha(tamanho_papel, orientacao, colunas)
    if largura_cm > largura_maxima:
        raise ValueError(
            f"Largura do modelo excede a área útil da folha. Máximo permitido: {largura_maxima} cm."
        )
    if altura_cm > altura_maxima:
        raise ValueError(
            f"Altura do modelo excede a área útil da folha. Máximo permitido: {altura_maxima} cm."
        )


class ModeloFichaEspelhoBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=255)
    descricao: str | None = Field(default=None, max_length=2000)
    campos: list[CampoFichaEspelho] = Field(default_factory=lambda: list(CAMPOS_PADRAO_FICHA_ESPELHO), min_length=1)
    tamanho_papel: Literal["A4", "CARTA"] = "A4"
    orientacao: Literal["RETRATO", "PAISAGEM"] = "RETRATO"
    colunas: int = Field(default=1, ge=1, le=2)
    largura_cm: float = Field(default=18.6, gt=0, le=200)
    altura_cm: float = Field(default=27.3, gt=0, le=200)
    ativo: bool = True

    @model_validator(mode="after")
    def validar_dimensoes(self):
        validar_dimensoes_modelo(
            self.tamanho_papel,
            self.orientacao,
            self.colunas,
            self.largura_cm,
            self.altura_cm,
        )
        return self


class ModeloFichaEspelhoCreate(ModeloFichaEspelhoBase):
    pass


class ModeloFichaEspelhoUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=255)
    descricao: str | None = Field(default=None, max_length=2000)
    campos: list[CampoFichaEspelho] | None = Field(default=None, min_length=1)
    tamanho_papel: Literal["A4", "CARTA"] | None = None
    orientacao: Literal["RETRATO", "PAISAGEM"] | None = None
    colunas: int | None = Field(default=None, ge=1, le=2)
    largura_cm: float | None = Field(default=None, gt=0, le=200)
    altura_cm: float | None = Field(default=None, gt=0, le=200)
    ativo: bool | None = None


class ModeloFichaEspelhoRead(ModeloFichaEspelhoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None


class ModeloFichaEspelhoPage(BaseModel):
    items: list[ModeloFichaEspelhoRead]
    total: int
    limit: int
    offset: int


class FichaEspelhoGerarRequest(BaseModel):
    modelo_id: int
    unidade_ids: list[int] = Field(..., min_length=1, max_length=200)


class FichaEspelhoInstituicao(BaseModel):
    nome: str | None = None
    logotipo_data_url: str | None = None


class FichaEspelhoDados(BaseModel):
    unidade_id: int
    unidade_produtora: str | None = None
    fundo: str | None = None
    classe: str | None = None
    subclasse: str | None = None
    descricao_conteudo: str | None = None
    data_limite: str | None = None
    identificador_caixa: str
    codigo_barras: str | None = None


class FichaEspelhoGerada(BaseModel):
    modelo: ModeloFichaEspelhoRead
    instituicao: FichaEspelhoInstituicao
    fichas: list[FichaEspelhoDados]
