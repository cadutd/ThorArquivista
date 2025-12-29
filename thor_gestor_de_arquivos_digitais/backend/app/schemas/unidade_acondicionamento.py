from __future__ import annotations

from pydantic import BaseModel, Field
from app.models.enums import TipoSuporte, TipoUnidade, NivelAcesso, StatusUnidade


class UnidadeAcondicionamentoBase(BaseModel):
    identificador: str = Field(..., max_length=255)
    titulo: str = Field(..., max_length=500)
    descricao: str | None = Field(default=None, max_length=2000)

    tipo_suporte: TipoSuporte
    tipo_unidade: TipoUnidade

    nivel_acesso: NivelAcesso = NivelAcesso.RESTRITO
    status: StatusUnidade = StatusUnidade.ATIVA

    id_unidade_pai: int | None = None
    id_representa: int | None = None


class UnidadeAcondicionamentoCreate(UnidadeAcondicionamentoBase):
    pass


class UnidadeAcondicionamentoUpdate(BaseModel):
    titulo: str | None = Field(default=None, max_length=500)
    descricao: str | None = Field(default=None, max_length=2000)
    nivel_acesso: NivelAcesso | None = None
    status: StatusUnidade | None = None
    id_unidade_pai: int | None = None
    id_representa: int | None = None


class UnidadeAcondicionamentoOut(UnidadeAcondicionamentoBase):
    id: int
    criado_em: str | None = None
    atualizado_em: str | None = None

    model_config = {"from_attributes": True}
