from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.unidade_acondicionamento import UnidadeAcondicionamentoOut

NIVEIS_DESCRICAO = ("1", "2", "2.5", "3", "3.5", "4", "5")
NORMAS_DESCRICAO = ("NOBRADE", "ISAD_G", "EAD2002")


class RegistroDescritivoBase(BaseModel):
    parent_id: uuid.UUID | None = None
    nivel: str = Field(..., pattern=r"^(1|2|2\.5|3|3\.5|4|5)$")
    norma: str = Field(default="NOBRADE", pattern=r"^(NOBRADE|ISAD_G|EAD2002)$")
    codigo_referencia: str = Field(..., min_length=1, max_length=255)
    titulo: str = Field(..., min_length=1, max_length=500)
    data_inicial: date | None = None
    data_final: date | None = None
    dimensao: str | None = None
    suporte: str | None = None
    produtor: str | None = None
    historia_administrativa: str | None = None
    historia_arquivistica: str | None = None
    procedencia: str | None = None
    ambito_conteudo: str | None = None
    avaliacao_eliminacao: str | None = None
    incorporacoes: str | None = None
    sistema_arranjo: str | None = None
    condicoes_acesso: str | None = None
    condicoes_reproducao: str | None = None
    idioma: str | None = None
    caracteristicas_tecnicas: str | None = None
    originais: str | None = None
    copias: str | None = None
    unidades_relacionadas: str | None = None
    publicacoes: str | None = None
    notas: str | None = None
    arquivista_responsavel: str | None = None
    regras_convencoes: str | None = None
    data_descricao: datetime | None = None
    assuntos: str | None = None
    pessoas: str | None = None
    locais: str | None = None
    entidades: str | None = None
    eventos: str | None = None

    @model_validator(mode="after")
    def validar_datas(self):
        if self.data_inicial and self.data_final and self.data_final < self.data_inicial:
            raise ValueError("Data final não pode ser anterior à data inicial.")
        return self


class RegistroDescritivoCreate(RegistroDescritivoBase):
    pass


class RegistroDescritivoUpdate(BaseModel):
    parent_id: uuid.UUID | None = None
    nivel: str | None = Field(default=None, pattern=r"^(1|2|2\.5|3|3\.5|4|5)$")
    norma: str | None = Field(default=None, pattern=r"^(NOBRADE|ISAD_G|EAD2002)$")
    codigo_referencia: str | None = Field(default=None, min_length=1, max_length=255)
    titulo: str | None = Field(default=None, min_length=1, max_length=500)
    data_inicial: date | None = None
    data_final: date | None = None
    dimensao: str | None = None
    suporte: str | None = None
    produtor: str | None = None
    historia_administrativa: str | None = None
    historia_arquivistica: str | None = None
    procedencia: str | None = None
    ambito_conteudo: str | None = None
    avaliacao_eliminacao: str | None = None
    incorporacoes: str | None = None
    sistema_arranjo: str | None = None
    condicoes_acesso: str | None = None
    condicoes_reproducao: str | None = None
    idioma: str | None = None
    caracteristicas_tecnicas: str | None = None
    originais: str | None = None
    copias: str | None = None
    unidades_relacionadas: str | None = None
    publicacoes: str | None = None
    notas: str | None = None
    arquivista_responsavel: str | None = None
    regras_convencoes: str | None = None
    data_descricao: datetime | None = None
    assuntos: str | None = None
    pessoas: str | None = None
    locais: str | None = None
    entidades: str | None = None
    eventos: str | None = None


class RegistroDescritivoRead(RegistroDescritivoBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    has_children: bool = False


class RegistroDescritivoTreeNode(BaseModel):
    id: uuid.UUID
    parent_id: uuid.UUID | None = None
    nivel: str
    norma: str
    codigo_referencia: str
    titulo: str
    children: list["RegistroDescritivoTreeNode"] = Field(default_factory=list)


class RegistroDescritivoBatchCreate(BaseModel):
    parent_id: uuid.UUID
    registros: list[RegistroDescritivoCreate] = Field(..., min_length=1, max_length=200)


class RegistroDescritivoMove(BaseModel):
    parent_id: uuid.UUID


class RegistroDescritivoDuplicate(BaseModel):
    parent_id: uuid.UUID | None = None
    titulo: str | None = Field(default=None, max_length=500)
    codigo_referencia: str | None = Field(default=None, max_length=255)


class EAD2002ImportResult(BaseModel):
    imported: int
    root_ids: list[uuid.UUID] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RegistroUnidadesAssociadasUpdate(BaseModel):
    unidades_ids: list[int] = Field(default_factory=list)


class RegistroUnidadesAssociadasRead(BaseModel):
    id_registro_descritivo: uuid.UUID
    unidades: list[UnidadeAcondicionamentoOut] = Field(default_factory=list)
